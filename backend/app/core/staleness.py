"""Stale POI computation (Phase 4.2.3).

A POI is considered *stale* when:
  - it has a ``last_verified_at`` that is older than ``STALE_AGE_DAYS``, AND
  - it has no active reports (an open report counts as "recent attention").

Brand-new POIs without ``last_verified_at`` are not stale.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

STALE_AGE_DAYS = 180


def compute_is_stale(
    *,
    last_verified_at: datetime | None,
    has_active_report: bool,
    now: datetime | None = None,
) -> bool:
    if last_verified_at is None:
        return False
    if has_active_report:
        return False
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=STALE_AGE_DAYS)
    return last_verified_at < cutoff
