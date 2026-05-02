"""JWT helpers for the smallmap session token (2.2.2).

We issue a short-ish JWT (default 30 days, configurable) carrying the user
UUID. The token is delivered to the browser as an HttpOnly cookie. Stateful
revocation isn't supported in v1 — clients drop the cookie on logout.
"""

from __future__ import annotations

import secrets
import time
import uuid

from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


def issue_session_token(user_id: uuid.UUID) -> str:
    """Mint a JWT for ``user_id``. Returns the encoded string."""
    now = int(time.time())
    payload: dict = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + settings.jwt_ttl_seconds,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_session_token(token: str) -> uuid.UUID | None:
    """Validate token and return user id, or None on any failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError:
        return None
    sub = payload.get("sub")
    if not isinstance(sub, str):
        return None
    try:
        return uuid.UUID(sub)
    except (ValueError, TypeError):
        return None


def make_oauth_state() -> str:
    """Random opaque string for OAuth CSRF protection."""
    return secrets.token_urlsafe(32)
