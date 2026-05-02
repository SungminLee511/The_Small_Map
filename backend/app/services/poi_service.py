from __future__ import annotations

import uuid

from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope, ST_X, ST_Y
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poi import POI, POIStatus, POIType
from app.schemas.poi import BBox, LatLng, POIDetail, POIRead

POI_LIMIT = 500


async def list_pois_in_bbox(
    session: AsyncSession,
    bbox: BBox,
    types: list[POIType] | None = None,
    limit: int = POI_LIMIT,
) -> tuple[list[POIRead], bool]:
    """Return POIs within bbox. Returns (items, truncated)."""
    envelope = ST_MakeEnvelope(bbox.west, bbox.south, bbox.east, bbox.north, 4326)

    stmt = (
        select(
            POI.id,
            POI.poi_type,
            POI.name,
            POI.attributes,
            POI.source,
            POI.status,
            POI.created_at,
            POI.updated_at,
            ST_Y(func.geometry(POI.location)).label("lat"),
            ST_X(func.geometry(POI.location)).label("lng"),
        )
        .where(
            ST_Intersects(POI.location, envelope),
            POI.status == POIStatus.active,
        )
    )

    if types:
        stmt = stmt.where(POI.poi_type.in_(types))

    stmt = stmt.limit(limit + 1)
    result = await session.execute(stmt)
    rows = result.all()

    truncated = len(rows) > limit
    rows = rows[:limit]

    items = [
        POIRead(
            id=row.id,
            poi_type=row.poi_type,
            location=LatLng(lat=row.lat, lng=row.lng),
            name=row.name,
            attributes=row.attributes,
            source=row.source,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]
    return items, truncated


async def get_poi_by_id(
    session: AsyncSession, poi_id: uuid.UUID
) -> POIDetail | None:
    """Return full POI detail or None if not found / soft-deleted."""
    stmt = (
        select(
            POI.id,
            POI.poi_type,
            POI.name,
            POI.attributes,
            POI.source,
            POI.status,
            POI.external_id,
            POI.last_verified_at,
            POI.verification_count,
            POI.created_at,
            POI.updated_at,
            ST_Y(func.geometry(POI.location)).label("lat"),
            ST_X(func.geometry(POI.location)).label("lng"),
        )
        .where(POI.id == poi_id, POI.status == POIStatus.active)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return POIDetail(
        id=row.id,
        poi_type=row.poi_type,
        location=LatLng(lat=row.lat, lng=row.lng),
        name=row.name,
        attributes=row.attributes,
        source=row.source,
        status=row.status,
        external_id=row.external_id,
        last_verified_at=row.last_verified_at,
        verification_count=row.verification_count,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
