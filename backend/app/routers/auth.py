"""Auth router: Kakao OAuth login + /me + logout (Phase 2.2.2)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.jwt_tokens import (
    decode_session_token,
    issue_session_token,
    make_oauth_state,
)
from app.core.kakao_oauth import (
    build_authorize_url,
    exchange_code_for_token,
    fetch_profile,
)
from app.db import get_session
from app.schemas.user import UserMe
from app.services.user_service import get_user_by_id, upsert_kakao_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

OAUTH_STATE_COOKIE = "smallmap_oauth_state"


def _set_session_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.jwt_ttl_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,  # type: ignore[arg-type]
        path="/",
    )


def _clear_session_cookie(resp: Response) -> None:
    resp.delete_cookie(
        key=settings.auth_cookie_name,
        path="/",
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,  # type: ignore[arg-type]
    )


@router.get("/kakao/authorize")
async def kakao_authorize() -> RedirectResponse:
    """Redirect the browser to Kakao's authorize endpoint."""
    if not settings.kakao_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kakao OAuth not configured",
        )
    state = make_oauth_state()
    url = build_authorize_url(
        client_id=settings.kakao_client_id,
        redirect_uri=settings.kakao_redirect_uri,
        state=state,
    )
    resp = RedirectResponse(url=url, status_code=302)
    # 5-minute state cookie — used to validate the callback
    resp.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        max_age=300,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,  # type: ignore[arg-type]
        path="/",
    )
    return resp


@router.get("/kakao/callback")
async def kakao_callback(
    code: str = Query(...),
    state: str = Query(...),
    request: Request = None,  # type: ignore[assignment]
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Handle the redirect from Kakao: exchange code, upsert user, set cookie."""
    if not settings.kakao_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kakao OAuth not configured",
        )

    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE) if request else None
    if not cookie_state or cookie_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid OAuth state",
        )

    try:
        access_token = await exchange_code_for_token(
            code=code,
            client_id=settings.kakao_client_id,
            client_secret=settings.kakao_client_secret,
            redirect_uri=settings.kakao_redirect_uri,
        )
        profile = await fetch_profile(access_token)
    except Exception as e:  # noqa: BLE001
        logger.exception("Kakao OAuth callback failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Kakao OAuth exchange failed",
        ) from e

    user = await upsert_kakao_user(session, profile)
    await session.commit()

    token = issue_session_token(user.id)
    resp = RedirectResponse(url=settings.frontend_base_url, status_code=302)
    _set_session_cookie(resp, token)
    # Clear the one-shot state cookie
    resp.delete_cookie(
        key=OAUTH_STATE_COOKIE,
        path="/",
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,  # type: ignore[arg-type]
    )
    return resp


@router.get("/me", response_model=UserMe)
async def get_me(
    smallmap_session: str | None = Cookie(None, alias=None),
    request: Request = None,  # type: ignore[assignment]
    session: AsyncSession = Depends(get_session),
) -> UserMe:
    """Return the currently logged-in user, or 401 if no/invalid cookie.

    NB: ``Cookie`` arg name uses the configured cookie name at request time,
    so we read it from ``request.cookies`` directly instead of a fixed
    parameter. The function arg is kept for FastAPI signature compat.
    """
    raw = request.cookies.get(settings.auth_cookie_name) if request else None
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated"
        )
    user_id = decode_session_token(raw)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )
    user = await get_user_by_id(session, user_id)
    if user is None or user.is_banned:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return UserMe.model_validate(user)


@router.post("/logout")
async def logout() -> Response:
    """Clear the session cookie. JWTs are stateless, so this is purely a hint
    to the browser; client should also drop any in-memory user state.
    """
    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_session_cookie(resp)
    return resp
