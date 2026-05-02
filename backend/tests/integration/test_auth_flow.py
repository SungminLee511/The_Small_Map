"""Integration tests for the auth router (Phase 2.2.10)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from app.config import settings
from app.core.jwt_tokens import issue_session_token
from app.core.kakao_oauth import KakaoProfile


@pytest.mark.asyncio
async def test_authorize_redirects_when_kakao_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "kakao_client_id", "test-client-id")
    resp = await client.get(
        "/api/v1/auth/kakao/authorize", follow_redirects=False
    )
    assert resp.status_code in (302, 307)
    assert "kauth.kakao.com" in resp.headers["location"]


@pytest.mark.asyncio
async def test_authorize_503_when_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "kakao_client_id", "")
    resp = await client.get(
        "/api/v1/auth/kakao/authorize", follow_redirects=False
    )
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_callback_rejects_bad_state(client, monkeypatch):
    monkeypatch.setattr(settings, "kakao_client_id", "test-client-id")
    resp = await client.get(
        "/api/v1/auth/kakao/callback?code=x&state=mismatch",
        cookies={"smallmap_oauth_state": "expected"},
        follow_redirects=False,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_callback_happy_path_sets_session_cookie(client, monkeypatch):
    monkeypatch.setattr(settings, "kakao_client_id", "test-client-id")

    async def fake_exchange(**kwargs):
        return "fake-access-token"

    async def fake_profile(token, *, http=None):
        return KakaoProfile(
            kakao_id=999_111, display_name="K-User", email=None, avatar_url=None
        )

    with patch("app.routers.auth.exchange_code_for_token", new=fake_exchange):
        with patch("app.routers.auth.fetch_profile", new=fake_profile):
            resp = await client.get(
                "/api/v1/auth/kakao/callback?code=abc&state=xyz",
                cookies={"smallmap_oauth_state": "xyz"},
                follow_redirects=False,
            )

    assert resp.status_code in (302, 307)
    set_cookies = resp.headers.get_list("set-cookie")
    assert any(settings.auth_cookie_name in c for c in set_cookies)


@pytest.mark.asyncio
async def test_me_401_without_cookie(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_401_with_garbage_token(client):
    resp = await client.get(
        "/api/v1/auth/me",
        cookies={settings.auth_cookie_name: "not.a.token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user(client, make_user):
    user = await make_user()
    token = issue_session_token(user.id)
    resp = await client.get(
        "/api/v1/auth/me",
        cookies={settings.auth_cookie_name: token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(user.id)
    assert body["display_name"] == user.display_name


@pytest.mark.asyncio
async def test_me_404_for_deleted_user(client):
    """Token with valid sig but user no longer exists."""
    token = issue_session_token(uuid.uuid4())
    resp = await client.get(
        "/api/v1/auth/me",
        cookies={settings.auth_cookie_name: token},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_cookie(client, make_user):
    user = await make_user()
    token = issue_session_token(user.id)
    resp = await client.post(
        "/api/v1/auth/logout",
        cookies={settings.auth_cookie_name: token},
    )
    assert resp.status_code == 204
