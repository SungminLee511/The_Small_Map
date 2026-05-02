"""Unit tests for auth dependencies (Phase 2.2.3)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.config import settings
from app.core.jwt_tokens import issue_session_token
from app.deps import (
    get_current_user,
    get_current_user_optional,
    require_admin,
)
from app.models.user import User


def _fake_user(**kw) -> User:
    base = dict(
        id=uuid.uuid4(),
        kakao_id=12345,
        display_name="Tester",
        email=None,
        avatar_url=None,
        reputation=0,
        is_admin=False,
        is_banned=False,
    )
    base.update(kw)
    return User(**base)


def _fake_request(cookie_value: str | None) -> MagicMock:
    req = MagicMock()
    req.cookies = {settings.auth_cookie_name: cookie_value} if cookie_value else {}
    return req


@pytest.mark.asyncio
async def test_optional_returns_none_without_cookie():
    req = _fake_request(None)
    out = await get_current_user_optional(req, session=AsyncMock())
    assert out is None


@pytest.mark.asyncio
async def test_optional_returns_none_with_garbage_token(monkeypatch):
    req = _fake_request("not.a.token")
    out = await get_current_user_optional(req, session=AsyncMock())
    assert out is None


@pytest.mark.asyncio
async def test_optional_returns_user_with_valid_token(monkeypatch):
    user = _fake_user()
    token = issue_session_token(user.id)

    async def fake_get(_session, uid):
        assert uid == user.id
        return user

    monkeypatch.setattr("app.deps.get_user_by_id", fake_get)
    out = await get_current_user_optional(_fake_request(token), session=AsyncMock())
    assert out is user


@pytest.mark.asyncio
async def test_optional_filters_banned_user(monkeypatch):
    banned = _fake_user(is_banned=True)
    token = issue_session_token(banned.id)

    async def fake_get(_session, _uid):
        return banned

    monkeypatch.setattr("app.deps.get_user_by_id", fake_get)
    out = await get_current_user_optional(_fake_request(token), session=AsyncMock())
    assert out is None


@pytest.mark.asyncio
async def test_required_raises_401_without_user():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(user=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_required_returns_user():
    user = _fake_user()
    out = await get_current_user(user=user)
    assert out is user


@pytest.mark.asyncio
async def test_require_admin_403_for_non_admin():
    user = _fake_user(is_admin=False)
    with pytest.raises(HTTPException) as exc:
        await require_admin(user=user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_returns_admin_user():
    user = _fake_user(is_admin=True)
    out = await require_admin(user=user)
    assert out is user
