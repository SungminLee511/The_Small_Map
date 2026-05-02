"""Admin-token-gated endpoints for ops tasks (e.g. trigger importers)."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query, status

from app.config import settings
from app.jobs.importer_scheduler import (
    build_default_importers,
    run_all_importers,
    run_importer_by_id,
)

router = APIRouter(tags=["admin"])


def _require_admin(x_admin_token: str | None) -> None:
    """Reject if admin token is unset or doesn't match."""
    if not settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin endpoints disabled (ADMIN_TOKEN not set)",
        )
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")


@router.post("/admin/run-importer")
async def admin_run_importer(
    source: str | None = Query(None, description="Source id; omit to run all"),
    x_admin_token: str | None = Header(None, alias="X-Admin-Token"),
):
    _require_admin(x_admin_token)

    if source is None:
        reports = await run_all_importers(settings)
        return {
            "ran": [{"source_id": r.source_id,
                     "created": r.created,
                     "updated": r.updated,
                     "unchanged": r.unchanged,
                     "removed": r.removed,
                     "errors": r.errors}
                    for r in reports]
        }

    valid_ids = {imp.source_id for imp in build_default_importers(settings)}
    if source not in valid_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown source: {source}",
        )

    report = await run_importer_by_id(source, settings)
    return {
        "source_id": report.source_id,
        "created": report.created,
        "updated": report.updated,
        "unchanged": report.unchanged,
        "removed": report.removed,
        "errors": report.errors,
    }
