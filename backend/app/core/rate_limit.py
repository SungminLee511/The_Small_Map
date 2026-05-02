"""In-memory rolling-window rate limiter (Phase 2.2.9).

Suitable for single-instance staging. Multi-replica deployments should
swap this for Redis (e.g. ``slowapi`` + Redis backend) before launch.

Each action has a ``(max_calls, window_seconds)`` budget per user.
Exceeding it raises ``RateLimitExceeded`` carrying the seconds the
client should back off.
"""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Iterable


@dataclass(frozen=True)
class RateLimit:
    max_calls: int
    window_seconds: int


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int, action: str):
        super().__init__(
            f"rate limit exceeded for {action}; retry after {retry_after}s"
        )
        self.retry_after = retry_after
        self.action = action


# Default limits per action. Tweak via tests/config later.
DEFAULT_LIMITS: dict[str, RateLimit] = {
    "submit_poi": RateLimit(max_calls=10, window_seconds=24 * 3600),
    "confirm_poi": RateLimit(max_calls=50, window_seconds=24 * 3600),
    # Phase 3 — keep report submission tighter than POI submission since
    # spam reports are easy to file.
    "submit_report": RateLimit(max_calls=5, window_seconds=24 * 3600),
    "confirm_report": RateLimit(max_calls=50, window_seconds=24 * 3600),
}


class InMemoryRateLimiter:
    """Per-(user, action) sliding window. Thread-safe via a single lock."""

    def __init__(self, limits: dict[str, RateLimit] | None = None):
        self._limits = dict(limits) if limits is not None else dict(DEFAULT_LIMITS)
        self._buckets: dict[tuple[uuid.UUID, str], deque[float]] = {}
        self._lock = Lock()

    def configure(self, limits: dict[str, RateLimit]) -> None:
        with self._lock:
            self._limits = dict(limits)

    def reset(self, user_id: uuid.UUID | None = None) -> None:
        """Clear state. Useful in tests."""
        with self._lock:
            if user_id is None:
                self._buckets.clear()
                return
            for key in list(self._buckets.keys()):
                if key[0] == user_id:
                    self._buckets.pop(key, None)

    def hit(
        self,
        user_id: uuid.UUID,
        action: str,
        *,
        now: float | None = None,
    ) -> None:
        """Record a call; raise ``RateLimitExceeded`` if over budget.

        Always counts a successful call against the budget; if you'd rather
        only count successful business outcomes, call ``hit`` after the
        business logic succeeds.
        """
        cfg = self._limits.get(action)
        if cfg is None:
            return  # no limit configured = unlimited
        ts = now if now is not None else time.time()
        cutoff = ts - cfg.window_seconds
        with self._lock:
            bucket = self._buckets.setdefault((user_id, action), deque())
            self._evict(bucket, cutoff)
            if len(bucket) >= cfg.max_calls:
                oldest = bucket[0]
                retry_after = int(max(1, oldest + cfg.window_seconds - ts))
                raise RateLimitExceeded(retry_after=retry_after, action=action)
            bucket.append(ts)

    @staticmethod
    def _evict(bucket: deque[float], cutoff: float) -> None:
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

    def state(self, user_id: uuid.UUID, action: str) -> tuple[int, int]:
        """Return ``(used, max)`` for diagnostics."""
        cfg = self._limits.get(action)
        with self._lock:
            bucket = self._buckets.get((user_id, action))
            if bucket is None or cfg is None:
                return 0, (cfg.max_calls if cfg else 0)
            cutoff = time.time() - cfg.window_seconds
            self._evict(bucket, cutoff)
            return len(bucket), cfg.max_calls


# Module-level singleton — kept simple for v1. Tests may swap via ``set_limiter``.
_limiter = InMemoryRateLimiter()


def get_limiter() -> InMemoryRateLimiter:
    return _limiter


def set_limiter(limiter: InMemoryRateLimiter) -> None:
    global _limiter
    _limiter = limiter


def hit(user_id: uuid.UUID, action: str) -> None:
    _limiter.hit(user_id, action)


def known_actions() -> Iterable[str]:
    return list(_limiter._limits.keys())  # noqa: SLF001
