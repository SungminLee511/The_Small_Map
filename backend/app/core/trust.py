"""Trust thresholds (Phase 4.2.2).

The plan:
- ``rep < 0``  → cannot submit (only confirm)
- ``rep < -10`` → auto-ban
- ``rep > 50`` → trusted; their submissions auto-verify

Centralised here so endpoints/services never hard-code the constants.
"""

from __future__ import annotations

from enum import Enum

NO_SUBMIT_THRESHOLD = 0       # < this = no submit
AUTO_BAN_THRESHOLD = -10      # <= this = banned
TRUSTED_THRESHOLD = 50        # >= this = auto-verify on submit


class TrustTier(str, Enum):
    banned = "banned"
    no_submit = "no_submit"
    normal = "normal"
    trusted = "trusted"


def tier_for_reputation(rep: int) -> TrustTier:
    if rep <= AUTO_BAN_THRESHOLD:
        return TrustTier.banned
    if rep < NO_SUBMIT_THRESHOLD:
        return TrustTier.no_submit
    if rep >= TRUSTED_THRESHOLD:
        return TrustTier.trusted
    return TrustTier.normal


def can_submit(rep: int) -> bool:
    return tier_for_reputation(rep) not in (TrustTier.banned, TrustTier.no_submit)


def is_trusted(rep: int) -> bool:
    return tier_for_reputation(rep) == TrustTier.trusted


def should_auto_ban(rep: int) -> bool:
    return rep <= AUTO_BAN_THRESHOLD
