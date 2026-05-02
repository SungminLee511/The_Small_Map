from __future__ import annotations

import uuid
from dataclasses import dataclass

from geoalchemy2 import WKTElement
from geoalchemy2.functions import (
    ST_Distance,
    ST_DWithin,
    ST_Intersects,
    ST_MakeEnvelope,
    ST_X,
    ST_Y,
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo import haversine_m
from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus
from app.schemas.poi import BBox, LatLng, POIDetail, POIRead

POI_LIMIT = 500
DUPLICATE_RADIUS_M = 10
SUBMISSION_GPS_TOLERANCE_M = 50


@dataclass
class DuplicateNearby:
    poi_id: uuid.UUID
    distance_m: float


class SubmissionGPSTooFarError(Exception):
    """Raised when ``submitted_gps`` is more than 50m from claimed location."""

    def __init__(self, distance_m: float):
        super().__init__(f"submitted_gps is {distance_m:.1f}m from claimed location")
        self.distance_m = distance_m


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
            POI.verification_status,
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

    # Phase 3.3.3: bulk-load active report counts and merge in.
    from app.services.report_service import active_report_counts_for_pois

    counts = await active_report_counts_for_pois(
        session, [row.id for row in rows]
    )
    items = [
        POIRead(
            id=row.id,
            poi_type=row.poi_type,
            location=LatLng(lat=row.lat, lng=row.lng),
            name=row.name,
            attributes=row.attributes,
            source=row.source,
            status=row.status,
            verification_status=row.verification_status,
            active_report_count=counts.get(row.id, 0),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]
    return items, truncated


async def find_nearby_duplicate(
    session: AsyncSession,
    *,
    lat: float,
    lng: float,
    poi_type: POIType,
    radius_m: float = DUPLICATE_RADIUS_M,
) -> DuplicateNearby | None:
    """Return a same-type active POI within ``radius_m``, if any (closest)."""
    point = WKTElement(f"POINT({lng} {lat})", srid=4326)
    stmt = (
        select(
            POI.id,
            ST_Distance(POI.location, point).label("dist"),
        )
        .where(
            POI.poi_type == poi_type,
            POI.status == POIStatus.active,
            ST_DWithin(POI.location, point, radius_m),
        )
        .order_by("dist")
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return DuplicateNearby(poi_id=row.id, distance_m=float(row.dist))


async def create_user_submitted_poi(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    poi_type: POIType,
    lat: float,
    lng: float,
    submitted_lat: float,
    submitted_lng: float,
    name: str | None,
    attributes: dict | None,
) -> POI:
    """Create a new user-submitted POI. Caller must commit.

    Raises ``SubmissionGPSTooFarError`` if the submitted GPS is more than
    50m from the claimed location. Caller is responsible for the duplicate
    check via ``find_nearby_duplicate`` so it can return a friendly response
    to the client.
    """
    gps_offset = haversine_m(lat, lng, submitted_lat, submitted_lng)
    if gps_offset > SUBMISSION_GPS_TOLERANCE_M:
        raise SubmissionGPSTooFarError(gps_offset)

    poi = POI(
        id=uuid.uuid4(),
        poi_type=poi_type,
        location=WKTElement(f"POINT({lng} {lat})", srid=4326),
        name=name,
        attributes=attributes or {},
        source=f"user:{user_id}",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.unverified,
        verification_count=1,  # the submitter counts as 1
    )
    session.add(poi)
    await session.flush()
    return poi


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
            POI.verification_status,
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
    # Phase 3.3.3 — attach active report count and recent active reports
    from app.schemas.report import ReportRead
    from app.services.report_service import (
        active_report_count_for_poi,
        recent_active_reports_for_poi,
    )

    report_count = await active_report_count_for_poi(session, row.id)
    recent = await recent_active_reports_for_poi(session, row.id, limit=5)
    active_reports_payload = [
        ReportRead.model_validate(r).model_dump(mode="json") for r in recent
    ]

    return POIDetail(
        id=row.id,
        poi_type=row.poi_type,
        location=LatLng(lat=row.lat, lng=row.lng),
        name=row.name,
        attributes=row.attributes,
        source=row.source,
        status=row.status,
        verification_status=row.verification_status,
        external_id=row.external_id,
        last_verified_at=row.last_verified_at,
        verification_count=row.verification_count,
        active_report_count=report_count,
        active_reports=active_reports_payload,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
