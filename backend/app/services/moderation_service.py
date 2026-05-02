"""POI moderation service (Phase 2.2.8)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poi import POI, POIStatus, POIVerificationStatus
from app.models.reputation_event import ReputationEventType
from app.models.user import User
from app.schemas.poi import LatLng, POIDetail
from app.services.reputation_service import append_event


class POINotFound(Exception):
    pass


async def soft_delete_poi(
    session: AsyncSession,
    *,
    poi_id: uuid.UUID,
    admin_user_id: uuid.UUID,
    reason: str | None,
) -> POI:
    """Soft-delete a POI (status='removed' + audit columns).

    If the POI was a user submission still in unverified state at deletion
    time, the submitter takes a ``poi_submitted_rejected`` reputation hit
    (Phase 4.2.1).
    """
    poi = (
        await session.execute(select(POI).where(POI.id == poi_id))
    ).scalar_one_or_none()
    if poi is None:
        raise POINotFound(str(poi_id))

    was_unverified = poi.verification_status == POIVerificationStatus.unverified
    submitter_id = _submitter_id_from_source(poi.source)

    poi.status = POIStatus.removed
    poi.deleted_at = datetime.now(timezone.utc)
    poi.deletion_reason = (reason or "")[:500] or None
    poi.deleted_by_user_id = admin_user_id
    await session.flush()

    if was_unverified and submitter_id is not None:
        submitter = (
            await session.execute(select(User).where(User.id == submitter_id))
        ).scalar_one_or_none()
        if submitter is not None:
            await append_event(
                session,
                user=submitter,
                event_type=ReputationEventType.poi_submitted_rejected,
                ref_id=poi.id,
            )
    return poi


def _submitter_id_from_source(source: str) -> uuid.UUID | None:
    if not source.startswith("user:"):
        return None
    try:
        return uuid.UUID(source.split(":", 1)[1])
    except (ValueError, TypeError):
        return None


async def approve_poi(
    session: AsyncSession, *, poi_id: uuid.UUID
) -> POI:
    """Force-flip an unverified POI to verified (admin shortcut)."""
    poi = (
        await session.execute(select(POI).where(POI.id == poi_id))
    ).scalar_one_or_none()
    if poi is None:
        raise POINotFound(str(poi_id))
    poi.verification_status = POIVerificationStatus.verified
    poi.last_verified_at = datetime.now(timezone.utc)
    await session.flush()
    return poi


async def list_pois_for_moderation(
    session: AsyncSession,
    *,
    verification_status: POIVerificationStatus | None = None,
    include_deleted: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[POIDetail]:
    """Admin moderation queue. Default: only active rows."""
    stmt = select(
        POI.id,
        POI.poi_type,
        POI.name,
        POI.attributes,
        POI.source,
        POI.status,
        POI.verification_status,
        POI.external_id,
        POI.last_verified_at,
        POI.verification_count,
        POI.created_at,
        POI.updated_at,
        ST_Y(func.geometry(POI.location)).label("lat"),
        ST_X(func.geometry(POI.location)).label("lng"),
    )
    if not include_deleted:
        stmt = stmt.where(POI.status == POIStatus.active)
    if verification_status is not None:
        stmt = stmt.where(POI.verification_status == verification_status)
    stmt = stmt.order_by(POI.created_at.desc()).limit(limit).offset(offset)
    rows = (await session.execute(stmt)).all()
    return [
        POIDetail(
            id=r.id,
            poi_type=r.poi_type,
            location=LatLng(lat=r.lat, lng=r.lng),
            name=r.name,
            attributes=r.attributes,
            source=r.source,
            status=r.status,
            verification_status=r.verification_status,
            external_id=r.external_id,
            last_verified_at=r.last_verified_at,
            verification_count=r.verification_count,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]
