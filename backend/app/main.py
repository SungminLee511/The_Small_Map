from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.core.logging import setup_logging
from app.core.request_logging import RequestLoggingMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.security_startup import enforce_at_startup
from app.db import async_session_factory
from app.jobs.importer_scheduler import start_scheduler, stop_scheduler
from app.routers import admin, auth, me, notifications, pois, reports, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    enforce_at_startup(settings)
    start_scheduler(settings)
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(title="The Small Map", version="0.1.0", lifespan=lifespan)

# Security headers + structured request log run on every response. The
# CORS middleware must come last (i.e. wrapped outermost) so it can see
# the eventual response and rewrite the Access-Control-* headers.
app.add_middleware(SecurityHeadersMiddleware, hsts=(settings.app_env == "production"))
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pois.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(me.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/health/db")
async def health_db():
    """Liveness check that actually talks to Postgres.

    Returns 200 with ``{"status": "ok"}`` only when ``SELECT 1`` succeeds.
    Wrapped in its own session so it never reuses a poisoned connection.
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
    except Exception as e:  # noqa: BLE001
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={"status": "error", "error": str(e)[:200]},
        )

    if value != 1:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={"status": "error", "error": "unexpected SELECT 1 result"},
        )
    return {"status": "ok"}
