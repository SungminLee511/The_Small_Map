"""Integration tests for the auto-expiry tick (Phase 3.3.6 / 3.3.2)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import select

from app.models.notification import Notification, NotificationType
from app.models.poi import POI, POIStatus, POIType, POIVerificationStatus
from app.models.report import Report, ReportStatus, ReportType
from app.services.report_service import expire_due_reports


async def _setup(db_session, make_user):
    poi = POI(
        poi_type=POIType.toilet,
        location=WKTElement("POINT(126.92 37.55)", srid=4326),
        name="P",
        attributes={},
        source="seed",
        status=POIStatus.active,
        verification_status=POIVerificationStatus.verified,
    )
    db_session.add(poi)
    await db_session.commit()
    reporter = await make_user()
    return poi, reporter


@pytest.mark.asyncio
async def test_expire_flips_due_reports_only(db_session, make_user):
    poi, reporter = await _setup(db_session, make_user)
    now = datetime.now(timezone.utc)
    due = Report(
        poi_id=poi.id,
        reporter_id=reporter.id,
        report_type=ReportType.dirty,
        status=ReportStatus.active,
        expires_at=now - timedelta(minutes=5),
    )
    fresh = Report(
        poi_id=poi.id,
        reporter_id=reporter.id,
        report_type=ReportType.dirty,
        status=ReportStatus.active,
        expires_at=now + timedelta(days=1),
    )
    db_session.add_all([due, fresh])
    await db_session.commit()

    n = await expire_due_reports(db_session, now=now)
    await db_session.commit()
    assert n == 1

    # Verify
    refreshed_due = (
        await db_session.execute(select(Report).where(Report.id == due.id))
    ).scalar_one()
    refreshed_fresh = (
        await db_session.execute(select(Report).where(Report.id == fresh.id))
    ).scalar_one()
    assert refreshed_due.status == ReportStatus.expired.value
    assert refreshed_fresh.status == ReportStatus.active.value


@pytest.mark.asyncio
async def test_expiry_emits_notification_to_reporter(db_session, make_user):
    poi, reporter = await _setup(db_session, make_user)
    now = datetime.now(timezone.utc)
    db_session.add(
        Report(
            poi_id=poi.id,
            reporter_id=reporter.id,
            report_type=ReportType.dirty,
            status=ReportStatus.active,
            expires_at=now - timedelta(seconds=1),
        )
    )
    await db_session.commit()

    await expire_due_reports(db_session, now=now)
    await db_session.commit()

    notes = list(
        (
            await db_session.execute(
                select(Notification).where(
                    Notification.user_id == reporter.id,
                    Notification.type == NotificationType.report_expired,
                )
            )
        ).scalars()
    )
    assert len(notes) == 1


@pytest.mark.asyncio
async def test_expire_idempotent_second_run_zero(db_session, make_user):
    poi, reporter = await _setup(db_session, make_user)
    now = datetime.now(timezone.utc)
    db_session.add(
        Report(
            poi_id=poi.id,
            reporter_id=reporter.id,
            report_type=ReportType.dirty,
            status=ReportStatus.active,
            expires_at=now - timedelta(hours=1),
        )
    )
    await db_session.commit()

    n1 = await expire_due_reports(db_session, now=now)
    await db_session.commit()
    n2 = await expire_due_reports(db_session, now=now)
    await db_session.commit()
    assert n1 == 1
    assert n2 == 0
