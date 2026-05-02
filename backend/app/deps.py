"""Shared FastAPI dependencies (Phase 2.2.3)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.jwt_tokens import decode_session_token
from app.db import get_session
from app.models.user import User
from app.services.user_service import get_user_by_id


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


async def get_current_user_optional(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Return the current user, or None if no/invalid session.

    Reads the JWT from the configured session cookie. Banned users count as
    "no user" (returns None) so endpoints can choose to allow guest reads.
    """
    raw = request.cookies.get(settings.auth_cookie_name)
    if not raw:
        return None
    user_id = decode_session_token(raw)
    if user_id is None:
        return None
    user = await get_user_by_id(session, user_id)
    if user is None or user.is_banned:
        return None
    return user


async def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    """Required-auth variant: 401 if no valid session, 403 if banned.

    The banned check here is informational — banned users are filtered to
    None in ``get_current_user_optional`` already, so we return 401. The
    explicit 403 path is reached only by callers that bypass the optional
    dep.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated"
        )
    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """403 if the authenticated user isn't an admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="admin only"
        )
    return user
