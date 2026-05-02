"""Service layer for users (Phase 2.2.2)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.kakao_oauth import KakaoProfile
from app.models.user import User


async def get_user_by_id(
    session: AsyncSession, user_id: uuid.UUID
) -> User | None:
    return (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()


async def upsert_kakao_user(
    session: AsyncSession, profile: KakaoProfile
) -> User:
    """Find by ``kakao_id`` and update profile, or insert a new row."""
    existing = (
        await session.execute(
            select(User).where(User.kakao_id == profile.kakao_id)
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if existing is None:
        user = User(
            id=uuid.uuid4(),
            kakao_id=profile.kakao_id,
            display_name=profile.display_name,
            email=profile.email,
            avatar_url=profile.avatar_url,
            last_seen_at=now,
        )
        session.add(user)
        await session.flush()
        return user

    # Refresh profile fields if they changed
    existing.display_name = profile.display_name
    existing.email = profile.email
    existing.avatar_url = profile.avatar_url
    existing.last_seen_at = now
    return existing
