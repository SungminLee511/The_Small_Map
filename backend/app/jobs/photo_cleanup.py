"""Cleanup job for unclaimed photo uploads (Phase 2.2.5).

Pending uploads whose ``expires_at`` is in the past get their bytes deleted
from R2 (best-effort) and the row's ``status`` flipped to ``deleted``.

Wired into the same APScheduler instance the importer uses.
"""

from __future__ import annotations

import logging

from app.core import r2
from app.db import async_session_factory
from app.services.photo_service import (
    expired_pending_uploads,
    mark_deleted,
)

logger = logging.getLogger(__name__)


async def run_photo_cleanup(settings) -> dict:
    """Delete bytes for expired pending uploads. Returns counts."""
    deleted_bytes = 0
    deleted_rows = 0
    errors = 0
    async with async_session_factory() as session:
        rows = list(await expired_pending_uploads(session))
        ids_to_delete: list = []
        for row in rows:
            try:
                if settings.r2_account_id and settings.r2_access_key_id:
                    r2.delete_object(settings, row.object_key)
                    deleted_bytes += 1
            except Exception:  # noqa: BLE001
                logger.exception(
                    "R2 delete failed for upload %s key=%s", row.id, row.object_key
                )
                errors += 1
                continue
            ids_to_delete.append(row.id)
        deleted_rows = await mark_deleted(session, upload_ids=ids_to_delete)
        await session.commit()
    return {
        "expired_seen": len(rows),
        "r2_deleted": deleted_bytes,
        "rows_marked_deleted": deleted_rows,
        "errors": errors,
    }
