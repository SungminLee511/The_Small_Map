"""Notification endpoints (Phase 3.3.5)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.models.user import User
from app.schemas.report import NotificationRead
from app.services.notification_service import (
    NotificationNotFound,
    list_notifications_for_user,
    mark_all_read,
    mark_read,
    unread_count_for_user,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_my_notifications(
    only_unread: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    rows = await list_notifications_for_user(
        session, user_id=user.id, only_unread=only_unread, limit=limit
    )
    return [NotificationRead.model_validate(n) for n in rows]


@router.get("/unread-count")
async def my_unread_count(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    n = await unread_count_for_user(session, user_id=user.id)
    return {"unread": n}


@router.post(
    "/{notification_id}/read", response_model=NotificationRead
)
async def mark_one_read(
    notification_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        n = await mark_read(
            session, notification_id=notification_id, user_id=user.id
        )
    except NotificationNotFound:
        raise HTTPException(status_code=404, detail="notification not found")
    await session.commit()
    return NotificationRead.model_validate(n)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_my_read(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    await mark_all_read(session, user_id=user.id)
    await session.commit()
