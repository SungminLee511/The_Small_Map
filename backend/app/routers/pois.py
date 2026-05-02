from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.models.poi import POIType
from app.models.user import User
from app.schemas.poi import (
    BBox,
    POICreate,
    POICreateDuplicateResponse,
    POIDetail,
    POIListResponse,
)
from app.schemas.poi_attributes import validate_attributes
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
        )
    except SubmissionGPSTooFarError as e:
        raise HTTPException(
            status_code=422,
            detail=f"submitted_gps is {e.distance_m:.1f}m from claimed location (max 50m)",
        )

    await session.commit()

    detail = await get_poi_by_id(session, poi.id)
    if detail is None:
        # Should never happen — defensive only.
        raise HTTPException(status_code=500, detail="POI created but vanished")
    return detail
