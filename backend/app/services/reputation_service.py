"""Reputation event ledger (Phase 4.2.1).

All mutations to ``users.reputation`` go through ``append_event``: it
inserts a row in ``reputation_events`` AND mutates the cached column on
``users``. ``recompute_reputation_for_user`` is the nightly drift-fixer:
re-derives the cached value from the ledger.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reputation_event import (
    EVENT_DELTAS,
    ReputationEvent,
    ReputationEventType,
)
from app.models.user import User


async def append_event(
    session: AsyncSession,
    *,
    user: User,
    event_type: ReputationEventType,
    ref_id: uuid.UUID | None = None,
) -> ReputationEvent:
    """Insert a ledger row and bump the cached column. Caller commits."""
    delta = EVENT_DELTAS[event_type]
    event = ReputationEvent(
        id=uuid.uuid4(),
        user_id=user.id,
        event_type=event_type,
        delta=delta,
        ref_id=ref_id,
    )
    session.add(event)
    user.reputation = (user.reputation or 0) + delta
    await session.flush()
    return event


async def recompute_reputation_for_user(
    session: AsyncSession, *, user: User
) -> int:
    """Re-derive ``user.reputation`` from the ledger. Returns the new value."""
    res = await session.execute(
        select(func.coalesce(func.sum(ReputationEvent.delta), 0)).where(
            ReputationEvent.user_id == user.id
        )
    )
    total = int(res.scalar_one())
    user.reputation = total
    return total


async def reputation_history(
    session: AsyncSession, *, user_id: uuid.UUID, limit: int = 100
) -> Sequence[ReputationEvent]:
    res = await session.execute(
        select(ReputationEvent)
        .where(ReputationEvent.user_id == user_id)
        .order_by(ReputationEvent.created_at.desc())
        .limit(limit)
    )
    return list(res.scalars())
