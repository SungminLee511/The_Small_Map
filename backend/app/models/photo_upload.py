"""PhotoUpload model — server-side bookkeeping for presigned R2 uploads.

Phase 2.2.5. Lifecycle:
- ``pending``: presigned URL issued; client may PUT bytes to R2 within TTL
- ``claimed``: a POI submission referenced this upload; bytes verified and
  the object has been moved to its canonical key
- ``deleted``: cleanup job hard-deleted unclaimed bytes after TTL
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PhotoUploadStatus(str, enum.Enum):
    pending = "pending"
    claimed = "claimed"
    deleted = "deleted"


class PhotoUpload(Base):
    __tablename__ = "photo_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Where the bytes live in R2. Pending uploads use a "tmp/" prefix;
    # claim moves them to "photos/<uuid>.<ext>".
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            PhotoUploadStatus,
            name="photo_upload_status_enum",
            create_constraint=True,
        ),
        nullable=False,
        default=PhotoUploadStatus.pending,
    )
    claimed_by_poi_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pois.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_photo_uploads_status", "status"),
        Index("ix_photo_uploads_expires_at", "expires_at"),
    )
