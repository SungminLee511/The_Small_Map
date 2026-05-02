"""Report service (Phase 3.3.1, 3.3.4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.models.poi import POI, POIStatus
from app.models.report import (
    Report,
    ReportConfirmation,
    ReportStatus,
    ReportType,
)
from app.schemas.poi import BBox

REPORT_TTL_DAYS = 7
RESOLVE_OTHER_DELAY_HOURS = 24
REPORT_BBOX_LIMIT = 500


class POINotFound(Exception):
    pass


class ReportNotFound(Exception):
    pass


class CannotConfirmOwnReport(Exception):
    pass


class AlreadyConfirmed(Exception):
    pass


class ResolutionTooEarly(Exception):
    """Non-reporter trying to resolve before the 24h window passes."""

    def __init__(self, retry_after_seconds: int):
        super().__init__(
            f"only the reporter can resolve before {RESOLVE_OTHER_DELAY_HOURS}h"
        )
        self.retry_after_seconds = retry_after_seconds


@dataclass
class CreateReportInput:
    report_type: ReportType
    description: str | None
    photo_url: str | None


# --- Create / List -------------------------------------------------------


async def create_report(
    session: AsyncSession,
    *,
    poi_id: uuid.UUID,
    reporter_id: uuid.UUID,
    payload: CreateReportInput,
) -> Report:
    poi = (
        await session.execute(
            select(POI).where(POI.id == poi_id, POI.status == POIStatus.active)
        )
    ).scalar_one_or_none()
    if poi is None:
        raise POINotFound(str(poi_id))
    now = datetime.now(timezone.utc)
    report = Report(
        id=uuid.uuid4(),
        poi_id=poi.id,
        reporter_id=reporter_id,
        report_type=payload.report_type,
        description=payload.description,
        photo_url=payload.photo_url,
        status=ReportStatus.active,
        expires_at=now + timedelta(days=REPORT_TTL_DAYS),
    )
    session.add(report)
    await session.flush()
    return report


async def list_reports_for_poi(
    session: AsyncSession,
    *,
    poi_id: uuid.UUID,
    status_filter: ReportStatus | None = ReportStatus.active,
    limit: int = 50,
) -> list[Report]:
    stmt = select(Report).where(Report.poi_id == poi_id)
    if status_filter is not None:
        stmt = stmt.where(Report.status == status_filter)
    stmt = stmt.order_by(Report.created_at.desc()).limit(limit)
    return list((await session.execute(stmt)).scalars())


async def list_reports_in_bbox(
    session: AsyncSession,
    *,
    bbox: BBox,
    status_filter: ReportStatus | None = ReportStatus.active,
    limit: int = REPORT_BBOX_LIMIT,
) -> tuple[list[Report], bool]:
    envelope = ST_MakeEnvelope(bbox.west, bbox.south, bbox.east, bbox.north, 4326)
    stmt = (
        select(Report)
        .join(POI, POI.id == Report.poi_id)
        .where(ST_Intersects(POI.location, envelope))
    )
    if status_filter is not None:
        stmt = stmt.where(Report.status == status_filter)
    stmt = stmt.order_by(Report.created_at.desc()).limit(limit + 1)
    rows = list((await session.execute(stmt)).scalars())
    truncated = len(rows) > limit
    return rows[:limit], truncated


# --- Confirm / Resolve / Dismiss ----------------------------------------


async def confirm_report(
    session: AsyncSession, *, report_id: uuid.UUID, user_id: uuid.UUID
) -> Report:
    report = await _get_active_report(session, report_id)
    if report.reporter_id == user_id:
        raise CannotConfirmOwnReport()
    rc = ReportConfirmation(report_id=report.id, user_id=user_id)
    session.add(rc)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise AlreadyConfirmed()
    report.confirmation_count = (report.confirmation_count or 0) + 1
    return report


async def resolve_report(
    session: AsyncSession,
    *,
    report_id: uuid.UUID,
    user_id: uuid.UUID,
    resolution_note: str,
    photo_url: str | None = None,
) -> Report:
    """Reporter can resolve any time; others must wait 24h after creation."""
    report = await _get_active_report(session, report_id)
    now = datetime.now(timezone.utc)
    if report.reporter_id != user_id:
        elapsed = (now - report.created_at).total_seconds()
        threshold = RESOLVE_OTHER_DELAY_HOURS * 3600
        if elapsed < threshold:
            raise ResolutionTooEarly(retry_after_seconds=int(threshold - elapsed))

    report.status = ReportStatus.resolved
    report.resolved_at = now
    report.resolved_by = user_id
    report.resolution_note = resolution_note
    if photo_url is not None:
        report.photo_url = photo_url

    # Notify the original reporter (unless they resolved their own)
    if report.reporter_id != user_id:
        session.add(
            Notification(
                id=uuid.uuid4(),
                user_id=report.reporter_id,
                type=NotificationType.report_resolved,
                payload={
                    "report_id": str(report.id),
                    "poi_id": str(report.poi_id),
                    "resolved_by": str(user_id),
                    "note": resolution_note,
                },
            )
        )
    return report


async def dismiss_report(
    session: AsyncSession,
    *,
    report_id: uuid.UUID,
    admin_id: uuid.UUID,
    reason: str | None,
) -> Report:
    report = await _get_active_report(session, report_id)
    report.status = ReportStatus.dismissed
    report.resolved_at = datetime.now(timezone.utc)
    report.resolved_by = admin_id
    if reason:
        report.resolution_note = reason[:500]
    return report


# --- Auto-expire (3.3.2) -------------------------------------------------


async def expire_due_reports(session: AsyncSession, *, now: datetime | None = None) -> int:
    """Flip active reports past their TTL to ``expired`` and notify reporters.

    Returns the count of newly-expired rows. Idempotent: only matches active
    rows whose ``expires_at < now``.
    """
    cutoff = now or datetime.now(timezone.utc)
    # Fetch first so we can emit notifications in the same transaction
    due = list(
        (
            await session.execute(
                select(Report).where(
                    Report.status == ReportStatus.active,
                    Report.expires_at < cutoff,
                )
            )
        ).scalars()
    )
    for r in due:
        session.add(
            Notification(
                id=uuid.uuid4(),
                user_id=r.reporter_id,
                type=NotificationType.report_expired,
                payload={
                    "report_id": str(r.id),
                    "poi_id": str(r.poi_id),
                },
            )
        )
    if due:
        await session.execute(
            update(Report)
            .where(Report.id.in_([r.id for r in due]))
            .values(status=ReportStatus.expired)
        )
    return len(due)


# --- Aggregates for POI list/detail (3.3.3) ----------------------------


async def active_report_count_for_poi(
    session: AsyncSession, poi_id: uuid.UUID
) -> int:
    res = await session.execute(
        select(func.count(Report.id)).where(
            Report.poi_id == poi_id,
            Report.status == ReportStatus.active,
        )
    )
    return int(res.scalar_one() or 0)


async def active_report_counts_for_pois(
    session: AsyncSession, poi_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not poi_ids:
        return {}
    stmt = (
        select(Report.poi_id, func.count(Report.id))
        .where(
            Report.poi_id.in_(poi_ids),
            Report.status == ReportStatus.active,
        )
        .group_by(Report.poi_id)
    )
    rows = (await session.execute(stmt)).all()
    return {row[0]: int(row[1]) for row in rows}


async def recent_active_reports_for_poi(
    session: AsyncSession, poi_id: uuid.UUID, limit: int = 5
) -> list[Report]:
    stmt = (
        select(Report)
        .where(Report.poi_id == poi_id, Report.status == ReportStatus.active)
        .order_by(Report.created_at.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars())


# --- helpers ---


async def _get_active_report(
    session: AsyncSession, report_id: uuid.UUID
) -> Report:
    report = (
        await session.execute(
            select(Report).where(
                Report.id == report_id,
                Report.status == ReportStatus.active,
            )
        )
    ).scalar_one_or_none()
    if report is None:
        raise ReportNotFound(str(report_id))
    return report
