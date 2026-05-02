"""Unit tests for the in-memory rate limiter (Phase 2.2.9)."""

from __future__ import annotations

import uuid

import pytest

from app.core.rate_limit import (
    DEFAULT_LIMITS,
    InMemoryRateLimiter,
    RateLimit,
    RateLimitExceeded,
)


def test_default_limits_match_plan():
    assert DEFAULT_LIMITS["submit_poi"].max_calls == 10
    assert DEFAULT_LIMITS["submit_poi"].window_seconds == 24 * 3600
    assert DEFAULT_LIMITS["confirm_poi"].max_calls == 50


def test_below_limit_allows_calls():
    rl = InMemoryRateLimiter({"x": RateLimit(max_calls=3, window_seconds=60)})
    uid = uuid.uuid4()
    for i in range(3):
        rl.hit(uid, "x", now=1000.0 + i)


def test_exceeding_raises():
    rl = InMemoryRateLimiter({"x": RateLimit(max_calls=2, window_seconds=60)})
    uid = uuid.uuid4()
    rl.hit(uid, "x", now=1000.0)
    rl.hit(uid, "x", now=1001.0)
    with pytest.raises(RateLimitExceeded) as exc:
        rl.hit(uid, "x", now=1002.0)
    assert exc.value.retry_after >= 1
    assert exc.value.action == "x"


def test_window_slides_off_old_calls():
    rl = InMemoryRateLimiter({"x": RateLimit(max_calls=2, window_seconds=10)})
    uid = uuid.uuid4()
    rl.hit(uid, "x", now=1000.0)
    rl.hit(uid, "x", now=1005.0)
    # 11s after the first hit, the first should have aged out
    rl.hit(uid, "x", now=1011.0)


def test_unknown_action_unlimited():
    rl = InMemoryRateLimiter({})
    uid = uuid.uuid4()
    for i in range(100):
        rl.hit(uid, "no-cfg", now=float(i))


def test_per_user_buckets_isolated():
    rl = InMemoryRateLimiter({"x": RateLimit(max_calls=1, window_seconds=60)})
    a, b = uuid.uuid4(), uuid.uuid4()
    rl.hit(a, "x", now=1000.0)
    rl.hit(b, "x", now=1000.0)


def test_state_reports_used_count():
    rl = InMemoryRateLimiter({"x": RateLimit(max_calls=5, window_seconds=60)})
    uid = uuid.uuid4()
    rl.hit(uid, "x")
    rl.hit(uid, "x")
    used, mx = rl.state(uid, "x")
    assert used == 2
    assert mx == 5


def test_reset_clears_state():
    rl = InMemoryRateLimiter({"x": RateLimit(max_calls=1, window_seconds=60)})
    uid = uuid.uuid4()
    rl.hit(uid, "x")
    rl.reset(uid)
    rl.hit(uid, "x")  # would otherwise raise
