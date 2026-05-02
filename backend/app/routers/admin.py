"""Admin endpoints.

Two auth flavors:
- ``X-Admin-Token`` header — ops automation (cron, importer triggers).
- ``require_admin`` user dependency — interactive moderation by a logged-in
  user with ``users.is_admin = true`` (Phase 2.2.8).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.deps import require_admin
from app.jobs.importer_scheduler import (
    build_default_importers,
    run_all_importers,
    run_importer_by_id,
)
from app.models.poi import POIVerificationStatus
from app.models.user import User
from app.schemas.poi import POIDetail
from app.services.moderation_service import (
    POINotFound,
    approve_poi,
    list_pois_for_moderation,
    soft_delete_poi,
)

router = APIRouter(tags=["admin"])


def _require_admin(x_admin_token: str | None) -> None:
    """Reject if admin token is unset or doesn't match."""
    if not settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin endpoints disabled (ADMIN_TOKEN not set)",
        )
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")


@router.post("/admin/run-importer")
async def admin_run_importer(
    source: str | None = Query(None, description="Source id; omit to run all"),
    x_admin_token: str | None = Header(None, alias="X-Admin-Token"),
):
    _require_admin(x_admin_token)

    if source is None:
        reports = await run_all_importers(settings)
        return {
            "ran": [{"source_id": r.source_id,
                     "created": r.created,
                     "updated": r.updated,
                     "unchanged": r.unchanged,
                     "removed": r.removed,
                     "errors": r.errors}
                    for r in reports]
        }

    valid_ids = {imp.source_id for imp in build_default_importers(settings)}
    if source not in valid_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown source: {source}",
        )

    report = await run_importer_by_id(source, settings)
    return {
        "source_id": report.source_id,
        "created": report.created,
        "updated": report.updated,
        "unchanged": report.unchanged,
        "removed": report.removed,
        "errors": report.errors,
    }


# --- POI moderation (logged-in user with is_admin) -------------------------


@router.get("/admin/pois", response_model=list[POIDetail])
async def list_admin_pois(
    verification_status: POIVerificationStatus | None = Query(
        None, description="Filter by verification status"
    ),
    include_deleted: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_admin),
):
    return await list_pois_for_moderation(
        session,
        verification_status=verification_status,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
    )


@router.post("/admin/pois/{poi_id}/approve", response_model=POIDetail)
async def approve_admin_poi(
    poi_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_admin),
):
    try:
        await approve_poi(session, poi_id=poi_id)
    except POINotFound:
        raise HTTPException(status_code=404, detail="POI not found")
    await session.commit()
    queue = await list_pois_for_moderation(
        session, verification_status=None, include_deleted=True, limit=1, offset=0
    )
    # Re-fetch the moderated row
    rows = [p for p in queue if p.id == poi_id]
    if rows:
        return rows[0]
    # Fallback: re-query directly
    from app.services.poi_service import get_poi_by_id

    refreshed = await get_poi_by_id(session, poi_id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="POI not found")
    return refreshed


@router.post("/admin/pois/{poi_id}/reject", response_model=POIDetail)
async def reject_admin_poi(
    poi_id: uuid.UUID,
    payload: dict = Body(default_factory=dict),
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    """Reject = soft-delete the POI. ``payload.reason`` is recorded."""
    reason = payload.get("reason") if isinstance(payload, dict) else None
    try:
        poi = await soft_delete_poi(
            session,
            poi_id=poi_id,
            admin_user_id=admin.id,
            reason=reason if isinstance(reason, str) else None,
        )
    except POINotFound:
        raise HTTPException(status_code=404, detail="POI not found")
    await session.commit()
    return POIDetail(
        id=poi.id,
        poi_type=poi.poi_type,  # type: ignore[arg-type]
        location={"lat": 0.0, "lng": 0.0},  # placeholder; client doesn't need post-delete
        name=poi.name,
        attributes=poi.attributes or {},
        source=poi.source,
        status=poi.status,  # type: ignore[arg-type]
        verification_status=poi.verification_status,  # type: ignore[arg-type]
        external_id=poi.external_id,
        last_verified_at=poi.last_verified_at,
        verification_count=poi.verification_count,
        created_at=poi.created_at,
        updated_at=poi.updated_at,
    )
