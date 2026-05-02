"""Integration tests covering the reputation ledger end-to-end (Phase 4.2.5)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import select

from app.core.trust import AUTO_BAN_THRESHOLD
from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus
from app.models.report import Report, ReportStatus, ReportType
from app.models.reputation_event import (
    ReputationEvent,
    ReputationEventType,
)
from app.services.reputation_service import (
    append_event,
    recompute_reputation_for_user,
)


@pytest.mark.asyncio
async def test_append_event_writes_ledger_and_bumps_cache(
    db_session, make_user
):
    user = await make_user()
    await append_event(
        db_session,
        user=user,
        event_type=ReputationEventType.confirmation,
    )
    await db_session.commit()
    assert user.reputation == 1
    rows = list(
        (
            await db_session.execute(
                select(ReputationEvent).where(ReputationEvent.user_id == user.id)
            )
        ).scalars()
    )
    assert len(rows) == 1
    assert rows[0].delta == 1


@pytest.mark.asyncio
async def test_recompute_recovers_drift(db_session, make_user):
    user = await make_user()
    await append_event(
        db_session, user=user, event_type=ReputationEventType.confirmation
    )
    await append_event(
        db_session, user=user, event_type=ReputationEventType.confirmation
    )
    await db_session.commit()

    # Simulate drift
    user.reputation = 999
    db_session.add(user)
    await db_session.commit()

    n = await recompute_reputation_for_user(db_session, user=user)
    await db_session.commit()
    assert n == 2
    assert user.reputation == 2


@pytest.mark.asyncio
async def test_auto_ban_at_threshold(db_session, make_user):
    user = await make_user()
    # Two report_dismissed_admin events: -5 + -5 = -10 → ban
    for _ in range(2):
        await append_event(
            db_session,
            user=user,
            event_type=ReputationEventType.report_dismissed_admin,
        )
    await db_session.commit()
    assert user.reputation == AUTO_BAN_THRESHOLD
    assert user.is_banned is True


@pytest.mark.asyncio
async def test_no_submit_blocks_negative_rep(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    user.reputation = -1
    db_session.add(user)
    await db_session.commit()

    payload = {
        "poi_type": "toilet",
        "location": {"lat": 37.566535, "lng": 126.901320},
        "name": None,
        "attributes": {},
        "submitted_gps": {
            "lat": 37.566535,
            "lng": 126.901320,
            "accuracy_m": 10,
        },
    }
    resp = await client.post(
        "/api/v1/pois", json=payload, cookies=auth_cookie(user)
    )
    assert resp.status_code == 403
    assert "reputation" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_trusted_user_submission_auto_verifies(
    client, db_session, make_user, auth_cookie
):
    trusted = await make_user()
    trusted.reputation = 100
    db_session.add(trusted)
    await db_session.commit()

    payload = {
        "poi_type": "toilet",
        "location": {"lat": 37.55, "lng": 126.92},
        "name": "trusted submission",
        "attributes": {},
        "submitted_gps": {"lat": 37.55, "lng": 126.92, "accuracy_m": 10},
    }
    resp = await client.post(
        "/api/v1/pois", json=payload, cookies=auth_cookie(trusted)
    )
    assert resp.status_code == 201
    assert resp.json()["verification_status"] == "verified"


@pytest.mark.asyncio
async def test_admin_dismiss_logs_dismissed_event(
    client, db_session, make_user, auth_cookie
):
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.55)", srid=4326),
        attributes={},
        source="seed",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.verified,
    )
    db_session.add(poi)
    await db_session.commit()

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

    admin = await make_user(is_admin=True)
    resp = await client.post(
        f"/api/v1/reports/{r.id}/dismiss",
        json={"reason": "spam"},
        cookies=auth_cookie(admin),
    )
    assert resp.status_code == 200

    events = list(
        (
            await db_session.execute(
                select(ReputationEvent).where(
                    ReputationEvent.user_id == reporter.id,
                    ReputationEvent.event_type
                    == ReputationEventType.report_dismissed_admin,
                )
            )
        ).scalars()
    )
    assert len(events) == 1
    assert events[0].delta == -5


@pytest.mark.asyncio
async def test_unverified_user_poi_rejection_logs_rejected_event(
    client, db_session, make_user, auth_cookie
):
    submitter = await make_user()
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.9 37.55)", srid=4326),
        attributes={},
        source=f"user:{submitter.id}",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.unverified,
    )
    db_session.add(poi)
    await db_session.commit()

    admin = await make_user(is_admin=True)
    resp = await client.post(
        f"/api/v1/admin/pois/{poi.id}/reject",
        json={"reason": "duplicate"},
        cookies=auth_cookie(admin),
    )
    assert resp.status_code == 200

    events = list(
        (
            await db_session.execute(
                select(ReputationEvent).where(
                    ReputationEvent.user_id == submitter.id,
                    ReputationEvent.event_type
                    == ReputationEventType.poi_submitted_rejected,
                )
            )
        ).scalars()
    )
    assert len(events) == 1
