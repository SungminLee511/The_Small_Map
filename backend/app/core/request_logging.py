"""Request-logging middleware — Phase 5.1.

Logs one structured line per HTTP request with::

    method, path, status, latency_ms, user_id, client_ip, request_id

We deliberately do **not** log request bodies (could contain photos,
location, attribute payloads) or response bodies. Only the route key.

The middleware also sets ``X-Request-Id`` on the response so a client can
quote it when reporting a bug.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger("smallmap.request")

# Paths we don't want to spam the logs with (1/sec health checks).
_QUIET_PATHS = {"/api/v1/health", "/api/v1/health/db"}


def _client_ip(request: Request) -> str | None:
    # Trust X-Forwarded-For only if a proxy has set it. The platform
    # (Fly.io / Railway / Cloudflare) controls the LB, so the leftmost
    # value is the real client.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def _user_id_from_request(request: Request) -> str | None:
    # ``app.deps.get_current_user_optional`` does not stash the user on
    # ``request.state`` today — keep the read defensive so we don't break
    # if that changes later.
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    uid = getattr(user, "id", None)
    return str(uid) if uid is not None else None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id

        start = time.perf_counter()
        status_code = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-Id"] = request_id
            return response
        finally:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            path = request.url.path
            if path in _QUIET_PATHS and status_code < 400:
                # Drop healthy probe noise; still log when they fail.
                pass
            else:
                log.info(
                    "request",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": path,
                        "status": status_code,
                        "latency_ms": latency_ms,
                        "user_id": _user_id_from_request(request),
                        "client_ip": _client_ip(request),
                    },
                )

