"""Integration tests for POST /api/v1/pois/{id}/confirm (Phase 2.2.10)."""

from __future__ import annotations

import pytest
from geoalchemy2 import WKTElement

from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus


async def _make_user_poi(db_session, submitter_id):
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.55)", srid=4326),
        name="Submitted",
        attributes={},
        source=f"user:{submitter_id}",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.unverified,
        verification_count=1,
    )
    db_session.add(poi)
    await db_session.commit()
    return poi


@pytest.mark.asyncio
async def test_confirm_requires_auth(client, db_session, make_user):
    submitter = await make_user()
    poi = await _make_user_poi(db_session, submitter.id)
    resp = await client.post(f"/api/v1/pois/{poi.id}/confirm")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_confirm_404_unknown_poi(client, make_user, auth_cookie):
    import uuid as _uuid

    user = await make_user()
    resp = await client.post(
        f"/api/v1/pois/{_uuid.uuid4()}/confirm", cookies=auth_cookie(user)
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_confirm_rejects_own_submission(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    poi = await _make_user_poi(db_session, user.id)
    resp = await client.post(
        f"/api/v1/pois/{poi.id}/confirm", cookies=auth_cookie(user)
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_confirm_idempotent_per_user(
    client, db_session, make_user, auth_cookie
):
    submitter = await make_user()
    poi = await _make_user_poi(db_session, submitter.id)
    other = await make_user()
    cookies = auth_cookie(other)

    resp1 = await client.post(f"/api/v1/pois/{poi.id}/confirm", cookies=cookies)
    assert resp1.status_code == 200
    resp2 = await client.post(f"/api/v1/pois/{poi.id}/confirm", cookies=cookies)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_verification_threshold_transition(
    client, db_session, make_user, auth_cookie
):
    submitter = await make_user()
    poi = await _make_user_poi(db_session, submitter.id)
    a = await make_user()
    b = await make_user()

    r1 = await client.post(
        f"/api/v1/pois/{poi.id}/confirm", cookies=auth_cookie(a)
    )
    assert r1.status_code == 200
    assert r1.json()["verification_status"] == "unverified"

    r2 = await client.post(
        f"/api/v1/pois/{poi.id}/confirm", cookies=auth_cookie(b)
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["verification_status"] == "verified"
    assert body["flipped_to_verified"] is True
