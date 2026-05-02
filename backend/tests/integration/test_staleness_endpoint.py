"""Integration tests verifying is_stale appears on /pois responses
(Phase 4.2.5 / 4.2.3)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from geoalchemy2 import WKTElement

from app.core.staleness import STALE_AGE_DAYS
from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus


async def _seed_poi(db_session, *, last_verified_at):
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.92 37.55)", srid=4326),
        attributes={},
        source="seoul.public_toilets",
        external_id="EXT-1",
        last_verified_at=last_verified_at,
        verification_count=1,
        status=POIStatus.active,
        verification_status=POIVerificationStatus.verified,
    )
    db_session.add(poi)
    await db_session.commit()
    return poi


@pytest.mark.asyncio
async def test_old_poi_marked_stale(client, db_session):
    old = datetime.now(timezone.utc) - timedelta(days=STALE_AGE_DAYS + 5)
    poi = await _seed_poi(db_session, last_verified_at=old)
    resp = await client.get(f"/api/v1/pois/{poi.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_stale"] is True


@pytest.mark.asyncio
async def test_recent_poi_not_stale(client, db_session):
    recent = datetime.now(timezone.utc) - timedelta(days=30)
    poi = await _seed_poi(db_session, last_verified_at=recent)
    resp = await client.get(f"/api/v1/pois/{poi.id}")
    assert resp.json()["is_stale"] is False


@pytest.mark.asyncio
async def test_bbox_response_includes_is_stale(client, db_session):
    old = datetime.now(timezone.utc) - timedelta(days=STALE_AGE_DAYS + 5)
    await _seed_poi(db_session, last_verified_at=old)
    resp = await client.get(
        "/api/v1/pois?bbox=126.91,37.54,126.93,37.56"
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert items[0]["is_stale"] is True
