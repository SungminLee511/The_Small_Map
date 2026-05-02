"""Notification queries (Phase 3.3.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationNotFound(Exception):
    pass


async def list_notifications_for_user(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    only_unread: bool = False,
    limit: int = 50,
) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if only_unread:
        stmt = stmt.where(Notification.read_at.is_(None))
    stmt = stmt.order_by(desc(Notification.created_at)).limit(limit)
    return list((await session.execute(stmt)).scalars())


async def unread_count_for_user(
    session: AsyncSession, *, user_id: uuid.UUID
) -> int:
    from sqlalchemy import func

    res = await session.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
    )
    return int(res.scalar_one() or 0)


async def mark_read(
    session: AsyncSession,
    *,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Notification:
    n = (
        await session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if n is None:
        raise NotificationNotFound(str(notification_id))
    if n.read_at is None:
        n.read_at = datetime.now(timezone.utc)
    return n


async def mark_all_read(
    session: AsyncSession, *, user_id: uuid.UUID
) -> int:
    res = await session.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(timezone.utc))
    )
    return res.rowcount or 0
