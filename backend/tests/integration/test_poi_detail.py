"""Integration tests for GET /api/v1/pois/{id} (1.3.7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from geoalchemy2 import WKTElement

from app.models.poi import POI, POIStatus, POIType


@pytest.mark.asyncio
async def test_get_poi_happy_path(client, db_session):
    poi = POI(
        id=uuid.uuid4(),
        poi_type=POIType.toilet,
        name="Mapo HQ Toilet",
        location=WKTElement("POINT(126.901320 37.566535)", srid=4326),
        source="seoul.public_toilets",
        external_id="EXT-99",
        last_verified_at=datetime(2026, 4, 30, tzinfo=timezone.utc),
        verification_count=2,
        status=POIStatus.active,
        attributes={"accessibility": True, "is_free": True},
    )
    db_session.add(poi)
    await db_session.commit()

    resp = await client.get(f"/api/v1/pois/{poi.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(poi.id)
    assert body["poi_type"] == "toilet"
    assert body["name"] == "Mapo HQ Toilet"
    assert body["external_id"] == "EXT-99"
    assert body["verification_count"] == 2
    assert body["last_verified_at"].startswith("2026-04-30")
    assert body["attributes"]["accessibility"] is True
    assert abs(body["location"]["lat"] - 37.566535) < 1e-6
    assert abs(body["location"]["lng"] - 126.901320) < 1e-6


@pytest.mark.asyncio
async def test_get_poi_not_found(client):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/pois/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_poi_soft_deleted_returns_404(client, db_session):
    poi = POI(
        id=uuid.uuid4(),
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.5)", srid=4326),
        source="seed",
        status=POIStatus.removed,
        attributes={},
    )
    db_session.add(poi)
    await db_session.commit()

    resp = await client.get(f"/api/v1/pois/{poi.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_poi_invalid_uuid(client):
    resp = await client.get("/api/v1/pois/not-a-uuid")
    assert resp.status_code == 422
