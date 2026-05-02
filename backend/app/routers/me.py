"""Profile endpoints for the logged-in user (Phase 2.3.4 + 4.3.2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from geoalchemy2.functions import ST_X, ST_Y
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.models.poi import POI, POIStatus
from app.models.poi_confirmation import POIConfirmation
from app.models.reputation_event import ReputationEventType
from app.models.user import User
from app.schemas.poi import LatLng, POIDetail
from app.services.reputation_service import reputation_history

router = APIRouter(prefix="/me", tags=["me"])


class ReputationEventRead(BaseModel):
    id: uuid.UUID
    event_type: ReputationEventType
    delta: int
    ref_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/submissions", response_model=list[POIDetail])
async def list_my_submissions(
    limit: int = Query(50, ge=1, le=200),
    include_deleted: bool = Query(False),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """POIs whose ``source = user:<self>``."""
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
    ).where(POI.source == f"user:{user.id}")
    if not include_deleted:
        stmt = stmt.where(POI.status == POIStatus.active)
    stmt = stmt.order_by(POI.created_at.desc()).limit(limit)
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


@router.get("/confirmations", response_model=list[POIDetail])
async def list_my_confirmations(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """POIs that the user has confirmed at least once."""
    stmt = (
        select(
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
        .join(POIConfirmation, POIConfirmation.poi_id == POI.id)
        .where(
            POIConfirmation.user_id == user.id,
            POI.status == POIStatus.active,
        )
        .order_by(POIConfirmation.created_at.desc())
        .limit(limit)
    )
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


@router.get("/reputation", response_model=list[ReputationEventRead])
async def list_my_reputation_events(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Phase 4.3.2 — append-only reputation ledger for the current user."""
    rows = await reputation_history(session, user_id=user.id, limit=limit)
    return [ReputationEventRead.model_validate(r) for r in rows]
