"""Integration tests for admin moderation endpoints (Phase 2.2.10)."""

from __future__ import annotations

import pytest
from geoalchemy2 import WKTElement

from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus


async def _seed_poi(db_session, status=POIStatus.active, vs=POIVerificationStatus.unverified):
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.55)", srid=4326),
        name="Mod target",
        attributes={},
        source="user:00000000-0000-0000-0000-000000000001",
        status=status,
        verification_status=vs,
    )
    db_session.add(poi)
    await db_session.commit()
    return poi


@pytest.mark.asyncio
async def test_list_admin_pois_requires_admin(client, make_user, auth_cookie):
    user = await make_user(is_admin=False)
    resp = await client.get(
        "/api/v1/admin/pois", cookies=auth_cookie(user)
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_admin_pois_admin_sees_unverified(
    client, db_session, make_user, auth_cookie
):
    await _seed_poi(db_session)
    admin = await make_user(is_admin=True)
    resp = await client.get(
        "/api/v1/admin/pois?verification_status=unverified",
        cookies=auth_cookie(admin),
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_approve_flips_to_verified(
    client, db_session, make_user, auth_cookie
):
    poi = await _seed_poi(db_session)
    admin = await make_user(is_admin=True)
    resp = await client.post(
        f"/api/v1/admin/pois/{poi.id}/approve",
        cookies=auth_cookie(admin),
    )
    assert resp.status_code == 200
    assert resp.json()["verification_status"] == "verified"


@pytest.mark.asyncio
async def test_reject_soft_deletes(
    client, db_session, make_user, auth_cookie
):
    poi = await _seed_poi(db_session)
    admin = await make_user(is_admin=True)
    resp = await client.post(
        f"/api/v1/admin/pois/{poi.id}/reject",
        json={"reason": "duplicate"},
        cookies=auth_cookie(admin),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "removed"


@pytest.mark.asyncio
async def test_delete_poi_admin_only(
    client, db_session, make_user, auth_cookie
):
    poi = await _seed_poi(db_session)
    user = await make_user(is_admin=False)
    resp = await client.delete(
        f"/api/v1/pois/{poi.id}", cookies=auth_cookie(user)
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_poi_admin_works(
    client, db_session, make_user, auth_cookie
):
    poi = await _seed_poi(db_session)
    admin = await make_user(is_admin=True)
    resp = await client.delete(
        f"/api/v1/pois/{poi.id}?reason=spam", cookies=auth_cookie(admin)
    )
    assert resp.status_code == 204
    # Detail endpoint now 404s (status='removed')
    resp2 = await client.get(f"/api/v1/pois/{poi.id}")
    assert resp2.status_code == 404
