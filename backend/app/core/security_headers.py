"""Security-headers middleware — Phase 5.4.

Sets a conservative, API-friendly default:

- ``X-Content-Type-Options: nosniff``      — prevent MIME confusion
- ``X-Frame-Options: DENY``                — clickjacking
- ``Referrer-Policy: no-referrer``         — don't leak source URL
- ``Permissions-Policy`` (camera/mic/geo)  — only same-origin features
- ``Content-Security-Policy``              — JSON API; ``frame-ancestors 'none'``
- ``Strict-Transport-Security``            — only when ``hsts=True``
  (caller decides; recommended in production behind HTTPS)

The frontend is a separate origin (Vite dev / static host), so the CSP
intentionally has nothing to do with script execution — it only locks
down framing and form-action for the JSON API.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def _build_csp() -> str:
    # The API never serves HTML, so this is mostly defense-in-depth.
    return "; ".join(
        [
            "default-src 'none'",
            "frame-ancestors 'none'",
            "form-action 'none'",
            "base-uri 'none'",
        ]
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, hsts: bool = False) -> None:
        super().__init__(app)
        self._hsts = hsts
        self._csp = _build_csp()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        h = response.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "no-referrer")
        h.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(self), interest-cohort=()",
        )
        h.setdefault("Content-Security-Policy", self._csp)
        if self._hsts:
            h.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response
