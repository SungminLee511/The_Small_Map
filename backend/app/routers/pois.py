from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import r2
from app.core.rate_limit import RateLimitExceeded, hit as rate_hit
from app.core.trust import can_submit, is_trusted
from app.db import get_session
from app.deps import get_current_user, require_admin
from app.models.poi import POIType
from app.models.user import User
from app.schemas.poi import (
    BBox,
    POIConfirmResponse,
    POICreate,
    POICreateDuplicateResponse,
    POIDetail,
    POIListResponse,
    POIRemovalProposalBody,
    POIRemovalProposalResponse,
)
from app.schemas.poi_attributes import validate_attributes
from app.services.confirmation_service import (
    AlreadyConfirmed,
    CannotConfirmOwnSubmission,
    POINotFound,
    confirm_poi,
)
from app.services.moderation_service import (
    POINotFound as POINotFoundForDelete,
    soft_delete_poi,
)
from app.services.removal_service import (
    REMOVAL_THRESHOLD,
    AlreadyProposed,
    CannotProposeOwnSubmission,
    POINotFound as POINotFoundForRemoval,
    propose_removal,
)
from app.services.photo_service import (
    canonical_object_key,
    get_claimable_upload,
    mark_claimed,
)
from app.services.poi_service import (
    SubmissionGPSTooFarError,
    create_user_submitted_poi,
    find_nearby_duplicate,
    get_poi_by_id,
    list_pois_in_bbox,
)

router = APIRouter(tags=["pois"])


@router.get("/pois", response_model=POIListResponse)
async def get_pois(
    bbox: str = Query(..., description="west,south,east,north"),
    type: list[POIType] | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    # Parse bbox
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(status_code=422, detail="bbox must be 4 comma-separated floats")

    try:
        west, south, east, north = [float(p.strip()) for p in parts]
    except ValueError:
        raise HTTPException(status_code=422, detail="bbox values must be floats")

    if west >= east:
        raise HTTPException(status_code=422, detail="west must be less than east")
    if south >= north:
        raise HTTPException(status_code=422, detail="south must be less than north")
    if (east - west) > 0.5 or (north - south) > 0.5:
        raise HTTPException(status_code=422, detail="bbox span must be < 0.5 degrees")

    bbox_obj = BBox(west=west, south=south, east=east, north=north)
    items, truncated = await list_pois_in_bbox(session, bbox_obj, types=type)
    return POIListResponse(items=items, truncated=truncated)


@router.get("/pois/{poi_id}", response_model=POIDetail)
async def get_poi(
    poi_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    detail = await get_poi_by_id(session, poi_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="POI not found")
    return detail


@router.post(
    "/pois",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "A POI of the same type already exists nearby",
            "model": POICreateDuplicateResponse,
        },
        422: {"description": "Validation error (e.g. submitted GPS too far)"},
    },
)
async def submit_poi(
    payload: POICreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """User-submitted POI. Auth required.

    Server-side validation:
    - submitted_gps must be within 50m of the claimed location
    - reject if a POI of the same type exists within 10m → 409 with the
      existing POI id (frontend prompts user to confirm it instead)
    - photo_upload_id is accepted but only validated in Phase 2.2.5+
    """
    # Reject banned users defensively (get_current_user already filters)
    if user.is_banned:
        raise HTTPException(status_code=403, detail="banned")

    # Phase 4.2.2 trust gate — negative reputation = no submit
    if not can_submit(user.reputation or 0):
        raise HTTPException(
            status_code=403,
            detail="reputation too low to submit; you can still confirm",
        )

    # Rate limit (10/24h) — count this call before the business logic so a
    # burst of failures still consumes budget and discourages spam.
    try:
        rate_hit(user.id, "submit_poi")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit: {e.action}",
            headers={"Retry-After": str(e.retry_after)},
        )

    # Validate type-specific attributes
    try:
        validated_attrs = validate_attributes(payload.poi_type, payload.attributes)
    except Exception as e:  # pydantic ValidationError
        raise HTTPException(status_code=422, detail=str(e))

    # Duplicate-nearby check
    dup = await find_nearby_duplicate(
        session,
        lat=payload.location.lat,
        lng=payload.location.lng,
        poi_type=payload.poi_type,
    )
    if dup is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "duplicate": True,
                "existing_poi_id": str(dup.poi_id),
                "distance_m": round(dup.distance_m, 1),
            },
        )

    # Validate photo upload (if provided) before creating POI
    upload = None
    if payload.photo_upload_id is not None:
        upload = await get_claimable_upload(
            session, upload_id=payload.photo_upload_id, user_id=user.id
        )
        if upload is None:
            raise HTTPException(
                status_code=400,
                detail="photo upload not found, expired, or not yours",
            )

    try:
        poi = await create_user_submitted_poi(
            session,
            user_id=user.id,
            poi_type=payload.poi_type,
            lat=payload.location.lat,
            lng=payload.location.lng,
            submitted_lat=payload.submitted_gps.lat,
            submitted_lng=payload.submitted_gps.lng,
            name=payload.name,
            attributes=validated_attrs,
            auto_verify=is_trusted(user.reputation or 0),
        )
    except SubmissionGPSTooFarError as e:
        raise HTTPException(
            status_code=422,
            detail=f"submitted_gps is {e.distance_m:.1f}m from claimed location (max 50m)",
        )

    # Claim the photo: HEAD it on R2, magic-byte sniff, copy tmp/→photos/.
    if upload is not None:
        try:
            head = r2.head_object(settings, upload.object_key)
            if head is None:
                raise HTTPException(
                    status_code=400,
                    detail="photo bytes not uploaded (R2 HEAD missed)",
                )
            size = int(head.get("ContentLength") or 0)
            if size <= 0 or size > settings.photo_upload_max_bytes:
                raise HTTPException(
                    status_code=400, detail="photo too large or empty"
                )

            # Magic-byte sniff: don't trust the client-declared
            # Content-Type. ``get_object_prefix`` returns None if the key
            # vanished between HEAD and GET.
            prefix = r2.get_object_prefix(settings, upload.object_key, n_bytes=16)
            if not prefix or not r2.looks_like_image(prefix):
                raise HTTPException(
                    status_code=400,
                    detail="photo bytes are not a recognized image",
                )

            new_key = canonical_object_key(upload.id, upload.content_type)
            r2.copy_object(
                settings, src_key=upload.object_key, dest_key=new_key
            )
            r2.delete_object(settings, upload.object_key)
            await mark_claimed(
                session, upload=upload, poi_id=poi.id, new_object_key=new_key
            )
            poi.photo_url = r2.public_url_for(settings, new_key)
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=502, detail=f"photo claim failed: {e}"
            )

    await session.commit()

    # Schedule PIPA blur as a background task. Idempotent and self-contained
    # so a failure here doesn't block the response.
    if upload is not None:
        from app.jobs.photo_blur_task import blur_photo_for_poi

        background_tasks.add_task(blur_photo_for_poi, poi.id, settings)

    detail = await get_poi_by_id(session, poi.id)
    if detail is None:
        # Should never happen — defensive only.
        raise HTTPException(status_code=500, detail="POI created but vanished")
    return detail


@router.post("/pois/{poi_id}/confirm", response_model=POIConfirmResponse)
async def confirm_existing_poi(
    poi_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Confirm that a POI exists. Auth required, idempotent per user."""
    try:
        rate_hit(user.id, "confirm_poi")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit: {e.action}",
            headers={"Retry-After": str(e.retry_after)},
        )

    try:
        result = await confirm_poi(session, poi_id=poi_id, user=user)
    except POINotFound:
        raise HTTPException(status_code=404, detail="POI not found")
    except CannotConfirmOwnSubmission:
        raise HTTPException(
            status_code=400, detail="cannot confirm your own submission"
        )
    except AlreadyConfirmed:
        raise HTTPException(status_code=409, detail="already confirmed")

    await session.commit()
    return POIConfirmResponse(
        poi_id=result.poi_id,
        verification_count=result.verification_count,
        verification_status=result.verification_status,
        flipped_to_verified=result.flipped_to_verified,
    )


@router.post(
    "/pois/{poi_id}/propose-removal",
    response_model=POIRemovalProposalResponse,
)
async def propose_poi_removal(
    poi_id: uuid.UUID,
    body: POIRemovalProposalBody,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Mark a POI as no-longer-existing (Phase 4.2.4).

    Three independent proposals auto-soft-delete the POI. Idempotent
    per (poi, user). Banned and below-zero-rep users blocked.
    """
    if user.is_banned:
        raise HTTPException(status_code=403, detail="banned")
    if not can_submit(user.reputation or 0):
        raise HTTPException(
            status_code=403,
            detail="reputation too low to propose removal",
        )

    try:
        rate_hit(user.id, "propose_removal")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit: {e.action}",
            headers={"Retry-After": str(e.retry_after)},
        )

    try:
        result = await propose_removal(
            session,
            poi_id=poi_id,
            user_id=user.id,
            reason=body.reason,
        )
    except POINotFoundForRemoval:
        raise HTTPException(status_code=404, detail="POI not found")
    except CannotProposeOwnSubmission:
        raise HTTPException(
            status_code=400,
            detail="cannot propose removal of your own submission",
        )
    except AlreadyProposed:
        raise HTTPException(status_code=409, detail="already proposed")
    await session.commit()
    return POIRemovalProposalResponse(
        poi_id=result.poi_id,
        proposal_count=result.proposal_count,
        threshold=REMOVAL_THRESHOLD,
        soft_deleted=result.soft_deleted,
    )


@router.delete(
    "/pois/{poi_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def admin_delete_poi(
    poi_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
    reason: str | None = Query(None, description="Reason recorded on the POI"),
):
    """Admin-only soft delete (Phase 2.2.8)."""
    try:
        await soft_delete_poi(
            session, poi_id=poi_id, admin_user_id=admin.id, reason=reason
        )
    except POINotFoundForDelete:
        raise HTTPException(status_code=404, detail="POI not found")
    await session.commit()
