"""Constants & helper sanity for report_service (Phase 3.3.6 unit tests)."""

from __future__ import annotations

from app.services.report_service import (
    REPORT_TTL_DAYS,
    RESOLVE_OTHER_DELAY_HOURS,
    REPORT_BBOX_LIMIT,
)


def test_constants_match_plan():
    assert REPORT_TTL_DAYS == 7
    assert RESOLVE_OTHER_DELAY_HOURS == 24
    assert REPORT_BBOX_LIMIT == 500
