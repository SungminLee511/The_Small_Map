"""APScheduler-based monthly importer runner.

Wired into FastAPI's lifespan. The scheduler runs in-process; for multi-replica
deployments switch to an external cron / Celery / Arq.

The scheduler is opt-in via ``settings.importer_scheduler_enabled``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from app.db import async_session_factory
from app.importers.base import BaseImporter, ImportReport
from app.importers.seoul_public_toilets import SeoulPublicToiletsImporter
from app.importers.seoul_smoking_areas import (
    MapoSmokingAreasImporter,
    kakao_geocode,
)

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)


def build_default_importers(settings: "Settings") -> list[BaseImporter]:
    """Construct the canonical list of importers from settings."""
    csv_dir = Path(settings.importer_csv_dir) if settings.importer_csv_dir else None

    def _csv_for(source_id: str) -> str | None:
        if csv_dir is None:
            return None
        path = csv_dir / f"{source_id}.csv"
        return str(path) if path.exists() else None

    importers: list[BaseImporter] = [
        SeoulPublicToiletsImporter(csv_path=_csv_for("seoul.public_toilets")),
    ]

    geocoder: Callable | None = None
    if settings.kakao_rest_api_key:
        async def geocoder(addr: str):  # noqa: E306
            return await kakao_geocode(
                addr, rest_api_key=settings.kakao_rest_api_key
            )
    importers.append(
        MapoSmokingAreasImporter(
            csv_path=_csv_for("mapo.smoking_areas"),
            geocoder=geocoder,
        )
    )
    return importers


async def run_importer_by_id(source_id: str, settings: "Settings") -> ImportReport:
    """Run a single importer by source_id. Returns its ImportReport."""
    for imp in build_default_importers(settings):
        if imp.source_id == source_id:
            async with async_session_factory() as session:
                return await imp.run(session)
    return ImportReport(source_id=source_id, errors=[f"unknown source_id: {source_id}"])


async def run_all_importers(settings: "Settings") -> list[ImportReport]:
    reports: list[ImportReport] = []
    for imp in build_default_importers(settings):
        async with async_session_factory() as session:
            try:
                reports.append(await imp.run(session))
            except Exception as e:  # noqa: BLE001
                logger.exception("Importer %s failed: %s", imp.source_id, e)
                reports.append(
                    ImportReport(source_id=imp.source_id, errors=[f"crashed: {e}"])
                )
    return reports


# --- APScheduler glue ----------------------------------------------------

_scheduler = None


def start_scheduler(settings: "Settings") -> None:
    """Start the AsyncIOScheduler. Idempotent."""
    global _scheduler
    if _scheduler is not None:
        return
    if not settings.importer_scheduler_enabled:
        logger.info("Importer scheduler disabled via settings; not starting")
        return

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    sched = AsyncIOScheduler()
    # Monthly at 03:15 UTC on the 1st — quiet hour for Seoul (~12:15 KST).
    for imp in build_default_importers(settings):
        sched.add_job(
            _scheduled_run,
            trigger=CronTrigger(day=1, hour=3, minute=15),
            args=[imp.source_id, settings],
            id=f"importer:{imp.source_id}",
            replace_existing=True,
        )
    # Hourly cleanup of expired pending photo uploads (Phase 2.2.5).
    from app.jobs.photo_cleanup import run_photo_cleanup

    async def _photo_cleanup_tick() -> None:
        try:
            report = await run_photo_cleanup(settings)
            logger.info("photo_cleanup tick: %s", report)
        except Exception:  # noqa: BLE001
            logger.exception("photo_cleanup failed")

    sched.add_job(
        _photo_cleanup_tick,
        trigger=CronTrigger(minute=17),
        id="photo_cleanup",
        replace_existing=True,
    )

    # Every-15-min report auto-expiry (Phase 3.3.2)
    from app.jobs.report_expiry import run_report_expiry_tick

    async def _report_expiry_tick() -> None:
        try:
            await run_report_expiry_tick()
        except Exception:  # noqa: BLE001
            logger.exception("report_expiry tick crashed")

    sched.add_job(
        _report_expiry_tick,
        trigger=CronTrigger(minute="*/15"),
        id="report_expiry",
        replace_existing=True,
    )

    sched.start()
    _scheduler = sched
    logger.info("Importer scheduler started with %d jobs", len(sched.get_jobs()))


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


async def _scheduled_run(source_id: str, settings: "Settings") -> None:
    logger.info("Scheduled importer kicking off: %s", source_id)
    report = await run_importer_by_id(source_id, settings)
    logger.info("Scheduled importer done: %s", report)
