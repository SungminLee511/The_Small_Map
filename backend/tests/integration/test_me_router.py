"""Integration tests for /api/v1/me/* (Phase 2.3.4)."""

from __future__ import annotations

import pytest
from geoalchemy2 import WKTElement

from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus
from app.models.poi_confirmation import POIConfirmation


@pytest.mark.asyncio
async def test_submissions_requires_auth(client):
    resp = await client.get("/api/v1/me/submissions")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submissions_returns_only_users_pois(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    other = await make_user()
    mine = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.55)", srid=4326),
        name="My toilet",
        attributes={},
        source=f"user:{user.id}",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.unverified,
        verification_count=1,
    )
    theirs = POI(
        poi_type=POIType.bench,
        location=WKTElement("POINT(126.92 37.56)", srid=4326),
        name="Their bench",
        attributes={},
        source=f"user:{other.id}",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.unverified,
        verification_count=1,
    )
    db_session.add_all([mine, theirs])
    await db_session.commit()

    resp = await client.get(
        "/api/v1/me/submissions", cookies=auth_cookie(user)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "My toilet"


@pytest.mark.asyncio
async def test_confirmations_returns_my_confirmed_pois(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    submitter = await make_user()
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.55)", srid=4326),
        name="Confirmed",
        attributes={},
        source=f"user:{submitter.id}",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.unverified,
        verification_count=2,
    )
    db_session.add(poi)
    await db_session.commit()
    db_session.add(POIConfirmation(poi_id=poi.id, user_id=user.id))
    await db_session.commit()

    resp = await client.get(
        "/api/v1/me/confirmations", cookies=auth_cookie(user)
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == str(poi.id)


@pytest.mark.asyncio
async def test_submissions_excludes_deleted_by_default(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.55)", srid=4326),
        name="Deleted",
        attributes={},
        source=f"user:{user.id}",
        status=POIStatus.removed,
        verification_status=POIVerificationStatus.unverified,
    )
    db_session.add(poi)
    await db_session.commit()
    resp = await client.get(
        "/api/v1/me/submissions", cookies=auth_cookie(user)
    )
    assert resp.status_code == 200
    assert resp.json() == []
