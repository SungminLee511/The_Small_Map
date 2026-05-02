"""Kakao OAuth 2.0 client glue (2.2.2).

We use the *authorization code* grant. Flow:

1. Browser hits ``GET /api/v1/auth/kakao/authorize`` → server redirects to
   ``https://kauth.kakao.com/oauth/authorize`` with a random ``state``
   stored in a short-lived cookie.
2. Kakao redirects back to ``KAKAO_REDIRECT_URI`` (frontend) which forwards
   the ``code`` + ``state`` to ``GET /api/v1/auth/kakao/callback``.
3. Server checks state, exchanges code for an access token, fetches the
   profile from ``https://kapi.kakao.com/v2/user/me``, upserts the local
   ``users`` row, mints a JWT, sets it as an HttpOnly cookie, redirects
   the user to ``/``.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

KAKAO_AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"


@dataclass(frozen=True)
class KakaoProfile:
    kakao_id: int
    display_name: str
    email: str | None
    avatar_url: str | None


def build_authorize_url(
    *, client_id: str, redirect_uri: str, state: str, scope: str = "profile_nickname"
) -> str:
    """Compose the Kakao authorize URL the browser is redirected to."""
    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": scope,
    }
    return f"{KAKAO_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_token(
    *,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    http: httpx.AsyncClient | None = None,
) -> str:
    """Exchange an auth code for an access token. Returns the access token."""
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    if client_secret:
        data["client_secret"] = client_secret

    own_client = http is None
    client = http or httpx.AsyncClient(timeout=15.0)
    try:
        resp = await client.post(KAKAO_TOKEN_URL, data=data)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError("Kakao token exchange returned no access_token")
        return token
    finally:
        if own_client:
            await client.aclose()


async def fetch_profile(
    access_token: str, *, http: httpx.AsyncClient | None = None
) -> KakaoProfile:
    """Fetch the user profile from Kakao. Maps to our internal shape."""
    own_client = http is None
    client = http or httpx.AsyncClient(timeout=15.0)
    try:
        resp = await client.get(
            KAKAO_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        body = resp.json()
    finally:
        if own_client:
            await client.aclose()
    return _normalize_profile(body)


def _normalize_profile(body: dict) -> KakaoProfile:
    kakao_id = body.get("id")
    if not isinstance(kakao_id, int):
        raise RuntimeError("Kakao profile missing 'id'")
    account = body.get("kakao_account") or {}
    profile = account.get("profile") or {}
    display_name = (
        profile.get("nickname")
        or account.get("name")
        or f"kakao-{kakao_id}"
    )
    email = account.get("email")
    avatar_url = profile.get("profile_image_url") or profile.get("thumbnail_image_url")
    return KakaoProfile(
        kakao_id=int(kakao_id),
        display_name=str(display_name),
        email=email if isinstance(email, str) else None,
        avatar_url=avatar_url if isinstance(avatar_url, str) else None,
    )
