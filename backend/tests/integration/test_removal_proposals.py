"""Integration tests for /pois/{id}/propose-removal (Phase 4.2.5 / 4.2.4)."""

from __future__ import annotations

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import select

from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus


async def _seed_poi(db_session, *, source="seed"):
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.55)", srid=4326),
        attributes={},
        source=source,
        status=POIStatus.active,
        verification_status=POIVerificationStatus.verified,
    )
    db_session.add(poi)
    await db_session.commit()
    return poi


@pytest.mark.asyncio
async def test_propose_requires_auth(client, db_session):
    poi = await _seed_poi(db_session)
    resp = await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal", json={"reason": "gone"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_propose_happy_path(
    client, db_session, make_user, auth_cookie
):
    poi = await _seed_poi(db_session)
    user = await make_user()
    resp = await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal",
        json={"reason": "철거됨"},
        cookies=auth_cookie(user),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["proposal_count"] == 1
    assert body["threshold"] == 3
    assert body["soft_deleted"] is False


@pytest.mark.asyncio
async def test_propose_idempotent_per_user(
    client, db_session, make_user, auth_cookie
):
    poi = await _seed_poi(db_session)
    user = await make_user()
    cookies = auth_cookie(user)
    r1 = await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal",
        json={"reason": "x"},
        cookies=cookies,
    )
    assert r1.status_code == 200
    r2 = await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal",
        json={"reason": "x again"},
        cookies=cookies,
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_propose_rejects_own_submission(
    client, db_session, make_user, auth_cookie
):
    submitter = await make_user()
    poi = await _seed_poi(db_session, source=f"user:{submitter.id}")
    resp = await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal",
        json={},
        cookies=auth_cookie(submitter),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_three_proposals_auto_soft_delete(
    client, db_session, make_user, auth_cookie
):
    poi = await _seed_poi(db_session)
    a = await make_user()
    b = await make_user()
    c = await make_user()

    await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal",
        json={},
        cookies=auth_cookie(a),
    )
    await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal",
        json={},
        cookies=auth_cookie(b),
    )
    third = await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal",
        json={},
        cookies=auth_cookie(c),
    )
    assert third.status_code == 200
    assert third.json()["soft_deleted"] is True

    refreshed = (
        await db_session.execute(select(POI).where(POI.id == poi.id))
    ).scalar_one()
    assert refreshed.status == POIStatus.removed.value
    # Detail endpoint now 404s
    detail = await client.get(f"/api/v1/pois/{poi.id}")
    assert detail.status_code == 404


@pytest.mark.asyncio
async def test_propose_404_unknown_poi(client, make_user, auth_cookie):
    import uuid as _uuid

    user = await make_user()
    resp = await client.post(
        f"/api/v1/pois/{_uuid.uuid4()}/propose-removal",
        json={},
        cookies=auth_cookie(user),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_propose_blocks_negative_rep(
    client, db_session, make_user, auth_cookie
):
    poi = await _seed_poi(db_session)
    user = await make_user()
    user.reputation = -1
    db_session.add(user)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/pois/{poi.id}/propose-removal",
        json={},
        cookies=auth_cookie(user),
    )
    assert resp.status_code == 403
