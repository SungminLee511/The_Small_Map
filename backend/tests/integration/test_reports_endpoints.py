"""Integration tests for the reports router (Phase 3.3.6)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from geoalchemy2 import WKTElement

from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus
from app.models.report import Report, ReportStatus, ReportType


async def _make_poi(db_session, *, name="P"):
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.92 37.55)", srid=4326),
        name=name,
        attributes={},
        source="seed",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.verified,
    )
    db_session.add(poi)
    await db_session.commit()
    return poi


@pytest.mark.asyncio
async def test_submit_report_requires_auth(client, db_session):
    poi = await _make_poi(db_session)
    resp = await client.post(
        f"/api/v1/pois/{poi.id}/reports",
        json={"report_type": "out_of_order"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submit_report_happy_path(
    client, db_session, make_user, auth_cookie
):
    poi = await _make_poi(db_session)
    user = await make_user()
    resp = await client.post(
        f"/api/v1/pois/{poi.id}/reports",
        json={
            "report_type": "out_of_order",
            "description": "변기 막힘",
        },
        cookies=auth_cookie(user),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "active"
    assert body["report_type"] == "out_of_order"
    assert body["confirmation_count"] == 0
    # expires_at ≈ now + 7d
    expires = datetime.fromisoformat(body["expires_at"].replace("Z", "+00:00"))
    delta = expires - datetime.now(timezone.utc)
    assert timedelta(days=6) < delta < timedelta(days=8)


@pytest.mark.asyncio
async def test_submit_report_404_unknown_poi(
    client, make_user, auth_cookie
):
    import uuid as _uuid

    user = await make_user()
    resp = await client.post(
        f"/api/v1/pois/{_uuid.uuid4()}/reports",
        json={"report_type": "dirty"},
        cookies=auth_cookie(user),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_reports_for_poi_filters_active(
    client, db_session, make_user
):
    poi = await _make_poi(db_session)
    reporter = await make_user()
    now = datetime.now(timezone.utc)
    db_session.add_all([
        Report(
            poi_id=poi.id,
            reporter_id=reporter.id,
            report_type=ReportType.dirty,
            status=ReportStatus.active,
            expires_at=now + timedelta(days=7),
        ),
        Report(
            poi_id=poi.id,
            reporter_id=reporter.id,
            report_type=ReportType.dirty,
            status=ReportStatus.expired,
            expires_at=now - timedelta(days=1),
        ),
    ])
    await db_session.commit()

    resp = await client.get(f"/api/v1/pois/{poi.id}/reports")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_confirm_report_idempotent(
    client, db_session, make_user, auth_cookie
):
    poi = await _make_poi(db_session)
    reporter = await make_user()
    other = await make_user()
    r = Report(
        poi_id=poi.id,
        reporter_id=reporter.id,
        report_type=ReportType.dirty,
        status=ReportStatus.active,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(r)
    await db_session.commit()

    cookies = auth_cookie(other)
    resp1 = await client.post(
        f"/api/v1/reports/{r.id}/confirm", cookies=cookies
    )
    assert resp1.status_code == 200
    assert resp1.json()["confirmation_count"] == 1
    resp2 = await client.post(
        f"/api/v1/reports/{r.id}/confirm", cookies=cookies
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_confirm_report_rejects_own(
    client, db_session, make_user, auth_cookie
):
    poi = await _make_poi(db_session)
    reporter = await make_user()
    r = Report(
        poi_id=poi.id,
        reporter_id=reporter.id,
        report_type=ReportType.dirty,
        status=ReportStatus.active,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(r)
    await db_session.commit()
    resp = await client.post(
        f"/api/v1/reports/{r.id}/confirm", cookies=auth_cookie(reporter)
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_resolve_reporter_anytime(
    client, db_session, make_user, auth_cookie
):
    poi = await _make_poi(db_session)
    reporter = await make_user()
    r = Report(
        poi_id=poi.id,
        reporter_id=reporter.id,
        report_type=ReportType.dirty,
        status=ReportStatus.active,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(r)
    await db_session.commit()
    resp = await client.post(
        f"/api/v1/reports/{r.id}/resolve",
        json={"resolution_note": "치웠어요"},
        cookies=auth_cookie(reporter),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_resolve_other_user_blocked_within_24h(
    client, db_session, make_user, auth_cookie
):
    poi = await _make_poi(db_session)
    reporter = await make_user()
    bystander = await make_user()
    r = Report(
        poi_id=poi.id,
        reporter_id=reporter.id,
        report_type=ReportType.dirty,
        status=ReportStatus.active,
        # Just-created report
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(r)
    await db_session.commit()
    resp = await client.post(
        f"/api/v1/reports/{r.id}/resolve",
        json={"resolution_note": "이미 정리됨"},
        cookies=auth_cookie(bystander),
    )
    assert resp.status_code == 403
    assert "Retry-After" in resp.headers


@pytest.mark.asyncio
async def test_dismiss_admin_only(client, db_session, make_user, auth_cookie):
    poi = await _make_poi(db_session)
    reporter = await make_user()
    r = Report(
        poi_id=poi.id,
        reporter_id=reporter.id,
        report_type=ReportType.dirty,
        status=ReportStatus.active,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(r)
    await db_session.commit()

    user = await make_user(is_admin=False)
    resp = await client.post(
        f"/api/v1/reports/{r.id}/dismiss",
        json={"reason": "spam"},
        cookies=auth_cookie(user),
    )
    assert resp.status_code == 403

    admin = await make_user(is_admin=True)
    resp2 = await client.post(
        f"/api/v1/reports/{r.id}/dismiss",
        json={"reason": "spam"},
        cookies=auth_cookie(admin),
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "dismissed"


@pytest.mark.asyncio
async def test_bbox_endpoint_returns_active_reports(
    client, db_session, make_user
):
    poi = await _make_poi(db_session)
    reporter = await make_user()
    db_session.add(
        Report(
            poi_id=poi.id,
            reporter_id=reporter.id,
            report_type=ReportType.dirty,
            status=ReportStatus.active,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    await db_session.commit()

    resp = await client.get(
        "/api/v1/reports?bbox=126.91,37.54,126.93,37.56"
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_bbox_validates_span(client):
    resp = await client.get("/api/v1/reports?bbox=120,30,180,90")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_poi_detail_carries_active_reports(
    client, db_session, make_user
):
    poi = await _make_poi(db_session)
    reporter = await make_user()
    db_session.add(
        Report(
            poi_id=poi.id,
            reporter_id=reporter.id,
            report_type=ReportType.dirty,
            status=ReportStatus.active,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    await db_session.commit()
    resp = await client.get(f"/api/v1/pois/{poi.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active_report_count"] == 1
    assert len(body["active_reports"]) == 1
