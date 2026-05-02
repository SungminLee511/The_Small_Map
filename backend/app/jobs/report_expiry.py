"""15-minute cron tick that expires due reports (Phase 3.3.2)."""

from __future__ import annotations

import logging

from app.db import async_session_factory
from app.services.report_service import expire_due_reports

logger = logging.getLogger(__name__)


async def run_report_expiry_tick() -> int:
    async with async_session_factory() as session:
        try:
            n = await expire_due_reports(session)
            await session.commit()
            if n:
                logger.info("report_expiry: flipped %d active → expired", n)
            return n
        except Exception:  # noqa: BLE001
            logger.exception("report_expiry tick failed")
            await session.rollback()
            return 0
