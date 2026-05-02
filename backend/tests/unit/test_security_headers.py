"""Unit tests for SecurityHeadersMiddleware — Phase 5.4."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.core.security_headers import SecurityHeadersMiddleware


def _build_app(*, hsts: bool) -> Starlette:
    async def hello(_request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/x", hello)])
    app.add_middleware(SecurityHeadersMiddleware, hsts=hsts)
    return app


@pytest.mark.asyncio
async def test_baseline_security_headers_present():
    app = _build_app(hsts=False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/x")

    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in resp.headers["Content-Security-Policy"]
    assert "default-src 'none'" in resp.headers["Content-Security-Policy"]
    # HSTS off by default
    assert "Strict-Transport-Security" not in resp.headers


@pytest.mark.asyncio
async def test_hsts_emitted_when_enabled():
    app = _build_app(hsts=True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/x")

    assert "max-age=" in resp.headers["Strict-Transport-Security"]
    assert "includeSubDomains" in resp.headers["Strict-Transport-Security"]


@pytest.mark.asyncio
async def test_permissions_policy_locks_down_camera_mic():
    app = _build_app(hsts=False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/x")

    pp = resp.headers["Permissions-Policy"]
    assert "camera=()" in pp
    assert "microphone=()" in pp
