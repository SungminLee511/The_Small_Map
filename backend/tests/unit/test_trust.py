"""Unit tests for the trust thresholds (Phase 4.2.5 / 4.2.2)."""

from __future__ import annotations

from app.core.trust import (
    AUTO_BAN_THRESHOLD,
    NO_SUBMIT_THRESHOLD,
    TRUSTED_THRESHOLD,
    TrustTier,
    can_submit,
    is_trusted,
    should_auto_ban,
    tier_for_reputation,
)


def test_thresholds_match_plan():
    assert NO_SUBMIT_THRESHOLD == 0
    assert AUTO_BAN_THRESHOLD == -10
    assert TRUSTED_THRESHOLD == 50


def test_tier_normal():
    assert tier_for_reputation(0) == TrustTier.normal
    assert tier_for_reputation(49) == TrustTier.normal


def test_tier_no_submit_under_zero():
    assert tier_for_reputation(-1) == TrustTier.no_submit
    assert tier_for_reputation(-9) == TrustTier.no_submit


def test_tier_banned_at_threshold():
    assert tier_for_reputation(-10) == TrustTier.banned
    assert tier_for_reputation(-100) == TrustTier.banned


def test_tier_trusted_above_threshold():
    assert tier_for_reputation(50) == TrustTier.trusted
    assert tier_for_reputation(999) == TrustTier.trusted


def test_can_submit_truth_table():
    assert can_submit(0) is True
    assert can_submit(50) is True
    assert can_submit(-1) is False
    assert can_submit(-10) is False


def test_is_trusted_truth_table():
    assert is_trusted(49) is False
    assert is_trusted(50) is True


def test_should_auto_ban():
    assert should_auto_ban(-10) is True
    assert should_auto_ban(-9) is False
