"""Unit tests for RequestLoggingMiddleware — Phase 5.1."""

from __future__ import annotations

import logging

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.core.request_logging import RequestLoggingMiddleware


def _build_app() -> Starlette:
    async def hello(_request):
        return JSONResponse({"ok": True})

    async def boom(_request):
        raise RuntimeError("kaboom")

    app = Starlette(routes=[Route("/ok", hello), Route("/boom", boom)])
    app.add_middleware(RequestLoggingMiddleware)
    return app


@pytest.mark.asyncio
async def test_sets_request_id_header_on_response():
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/ok")

    assert resp.status_code == 200
    rid = resp.headers.get("X-Request-Id")
    assert rid and len(rid) >= 8


@pytest.mark.asyncio
async def test_propagates_incoming_request_id():
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/ok", headers={"X-Request-Id": "abc-123"})

    assert resp.headers.get("X-Request-Id") == "abc-123"


@pytest.mark.asyncio
async def test_logs_request_line(caplog):
    app = _build_app()
    transport = ASGITransport(app=app)
    with caplog.at_level(logging.INFO, logger="smallmap.request"):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.get("/ok")

    rec = next((r for r in caplog.records if r.name == "smallmap.request"), None)
    assert rec is not None
    assert getattr(rec, "method", None) == "GET"
    assert getattr(rec, "path", None) == "/ok"
    assert getattr(rec, "status", None) == 200
    assert isinstance(getattr(rec, "latency_ms", None), float)


@pytest.mark.asyncio
async def test_quiet_health_path_does_not_log(caplog):
    async def health(_request):
        return JSONResponse({"status": "ok"})

    app = Starlette(routes=[Route("/api/v1/health", health)])
    app.add_middleware(RequestLoggingMiddleware)
    transport = ASGITransport(app=app)
    with caplog.at_level(logging.INFO, logger="smallmap.request"):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.get("/api/v1/health")

    assert not [r for r in caplog.records if r.name == "smallmap.request"]
