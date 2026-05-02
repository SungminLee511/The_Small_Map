"""Photo upload bookkeeping (Phase 2.2.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.photo_upload import PhotoUpload, PhotoUploadStatus

# Allowed inbound content types. Magic-byte check still happens on claim.
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Extension chosen by content type for the canonical key after claim.
EXT_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _ext_for(content_type: str) -> str:
    return EXT_BY_CONTENT_TYPE.get(content_type, "bin")


def temp_object_key(upload_id: uuid.UUID, content_type: str) -> str:
    return f"tmp/{upload_id}.{_ext_for(content_type)}"


def canonical_object_key(upload_id: uuid.UUID, content_type: str) -> str:
    return f"photos/{upload_id}.{_ext_for(content_type)}"


async def create_pending_upload(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    content_type: str,
    ttl_seconds: int,
) -> PhotoUpload:
    """Insert a pending PhotoUpload row and flush. Caller commits."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"unsupported content type: {content_type}")

    upload_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    row = PhotoUpload(
        id=upload_id,
        user_id=user_id,
        object_key=temp_object_key(upload_id, content_type),
        content_type=content_type,
        status=PhotoUploadStatus.pending,
        expires_at=now + timedelta(seconds=ttl_seconds),
    )
    session.add(row)
    await session.flush()
    return row


async def get_claimable_upload(
    session: AsyncSession, *, upload_id: uuid.UUID, user_id: uuid.UUID
) -> PhotoUpload | None:
    """Return the upload row if it belongs to ``user_id`` and is still claimable."""
    row = (
        await session.execute(
            select(PhotoUpload).where(PhotoUpload.id == upload_id)
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    if row.user_id != user_id:
        return None
    if row.status != PhotoUploadStatus.pending:
        return None
    if row.expires_at is not None and row.expires_at < datetime.now(timezone.utc):
        return None
    return row


async def mark_claimed(
    session: AsyncSession,
    *,
    upload: PhotoUpload,
    poi_id: uuid.UUID,
    new_object_key: str,
) -> None:
    upload.status = PhotoUploadStatus.claimed
    upload.claimed_by_poi_id = poi_id
    upload.claimed_at = datetime.now(timezone.utc)
    upload.object_key = new_object_key
    await session.flush()


async def expired_pending_uploads(
    session: AsyncSession, *, now: datetime | None = None
) -> Iterable[PhotoUpload]:
    """Pending uploads whose TTL elapsed — ready for cleanup."""
    cutoff = now or datetime.now(timezone.utc)
    res = await session.execute(
        select(PhotoUpload).where(
            PhotoUpload.status == PhotoUploadStatus.pending,
            PhotoUpload.expires_at < cutoff,
        )
    )
    return list(res.scalars().all())


async def mark_deleted(
    session: AsyncSession, *, upload_ids: list[uuid.UUID]
) -> int:
    if not upload_ids:
        return 0
    res = await session.execute(
        update(PhotoUpload)
        .where(PhotoUpload.id.in_(upload_ids))
        .values(status=PhotoUploadStatus.deleted)
    )
    return res.rowcount or 0
