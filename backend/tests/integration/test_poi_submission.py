"""Integration tests for POST /api/v1/pois (Phase 2.2.10)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from geoalchemy2 import WKTElement

from app.config import settings
from app.models.photo_upload import PhotoUpload, PhotoUploadStatus
from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus


def _payload(**overrides) -> dict:
    base = {
        "poi_type": "toilet",
        "location": {"lat": 37.566535, "lng": 126.901320},
        "name": "User-submitted toilet",
        "attributes": {"is_free": True},
        "submitted_gps": {
            "lat": 37.566535,
            "lng": 126.901320,
            "accuracy_m": 12.0,
        },
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_submit_requires_auth(client):
    resp = await client.post("/api/v1/pois", json=_payload())
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submit_happy_path(client, make_user, auth_cookie):
    user = await make_user()
    resp = await client.post(
        "/api/v1/pois",
        json=_payload(),
        cookies=auth_cookie(user),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["verification_status"] == "unverified"
    assert body["source"] == f"user:{user.id}"
    assert body["verification_count"] == 1


@pytest.mark.asyncio
async def test_submit_rejects_gps_too_far(client, make_user, auth_cookie):
    user = await make_user()
    # ~1 km offset
    payload = _payload(
        submitted_gps={"lat": 37.575, "lng": 126.901320, "accuracy_m": 5}
    )
    resp = await client.post(
        "/api/v1/pois", json=payload, cookies=auth_cookie(user)
    )
    assert resp.status_code == 422
    assert "submitted_gps" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_submit_rejects_duplicate_within_10m(
    client, make_user, auth_cookie, db_session
):
    # Pre-seed an active toilet at the same coords
    existing = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.901320 37.566535)", srid=4326),
        name="Existing",
        attributes={},
        source="seed",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.verified,
    )
    db_session.add(existing)
    await db_session.commit()

    user = await make_user()
    resp = await client.post(
        "/api/v1/pois", json=_payload(), cookies=auth_cookie(user)
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["duplicate"] is True


@pytest.mark.asyncio
async def test_submit_rejects_unknown_photo_upload(
    client, make_user, auth_cookie
):
    import uuid as _uuid

    user = await make_user()
    payload = _payload(photo_upload_id=str(_uuid.uuid4()))
    resp = await client.post(
        "/api/v1/pois", json=payload, cookies=auth_cookie(user)
    )
    assert resp.status_code == 400
    assert "photo upload" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_submit_rejects_other_users_photo_upload(
    client, make_user, auth_cookie, db_session
):
    """A user can't claim someone else's pending upload."""
    owner = await make_user()
    other_user = await make_user()

    upload = PhotoUpload(
        user_id=owner.id,
        object_key=f"tmp/{owner.id}.jpg",
        content_type="image/jpeg",
        status=PhotoUploadStatus.pending,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db_session.add(upload)
    await db_session.commit()

    payload = _payload(photo_upload_id=str(upload.id))
    resp = await client.post(
        "/api/v1/pois", json=payload, cookies=auth_cookie(other_user)
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_submit_rate_limit_triggers_429(
    client, make_user, auth_cookie, monkeypatch
):
    """11th submission in 24h should 429 with Retry-After."""
    from app.core.rate_limit import RateLimit, get_limiter

    get_limiter().configure(
        {"submit_poi": RateLimit(max_calls=2, window_seconds=3600)}
    )
    user = await make_user()
    cookies = auth_cookie(user)

    # First two pass
    for i in range(2):
        payload = _payload(
            location={"lat": 37.5 + i * 0.01, "lng": 126.9 + i * 0.01},
            submitted_gps={
                "lat": 37.5 + i * 0.01,
                "lng": 126.9 + i * 0.01,
                "accuracy_m": 5,
            },
        )
        resp = await client.post("/api/v1/pois", json=payload, cookies=cookies)
        assert resp.status_code == 201, resp.text

    # Third is rate-limited
    payload = _payload(
        location={"lat": 37.6, "lng": 127.0},
        submitted_gps={"lat": 37.6, "lng": 127.0, "accuracy_m": 5},
    )
    resp = await client.post("/api/v1/pois", json=payload, cookies=cookies)
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


@pytest.mark.asyncio
async def test_banned_user_cannot_submit(client, make_user, auth_cookie, db_session):
    """Banned users are filtered to 'no user' by get_current_user_optional → 401."""
    user = await make_user()
    user.is_banned = True
    db_session.add(user)
    await db_session.commit()
    resp = await client.post(
        "/api/v1/pois", json=_payload(), cookies=auth_cookie(user)
    )
    # Banned user is dropped to 'no user' → 401
    assert resp.status_code in (401, 403)


# Reference settings to avoid unused-import warning
_ = settings
