"""Unit tests for compute_is_stale (Phase 4.2.5 / 4.2.3)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.staleness import STALE_AGE_DAYS, compute_is_stale


def test_no_last_verified_at_is_not_stale():
    assert compute_is_stale(last_verified_at=None, has_active_report=False) is False


def test_recent_verification_is_not_stale():
    now = datetime.now(timezone.utc)
    assert (
        compute_is_stale(
            last_verified_at=now - timedelta(days=10),
            has_active_report=False,
        )
        is False
    )


def test_old_verification_with_no_reports_is_stale():
    now = datetime.now(timezone.utc)
    assert (
        compute_is_stale(
            last_verified_at=now - timedelta(days=STALE_AGE_DAYS + 1),
            has_active_report=False,
        )
        is True
    )


def test_old_verification_but_active_reports_is_not_stale():
    now = datetime.now(timezone.utc)
    assert (
        compute_is_stale(
            last_verified_at=now - timedelta(days=STALE_AGE_DAYS + 1),
            has_active_report=True,
        )
        is False
    )


def test_exactly_at_cutoff_is_not_stale():
    fixed = datetime(2026, 5, 1, tzinfo=timezone.utc)
    cutoff = fixed - timedelta(days=STALE_AGE_DAYS)
    assert (
        compute_is_stale(
            last_verified_at=cutoff, has_active_report=False, now=fixed
        )
        is False
    )
