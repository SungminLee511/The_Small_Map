"""POI status reports (Phase 3 — the differentiator).

A ``Report`` is a transient issue tied to a POI. Auto-expires after 7 days.
``ReportConfirmation`` records "I see this too" corroborations.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ReportType(str, enum.Enum):
    out_of_order = "out_of_order"
    overflowing = "overflowing"
    dirty = "dirty"
    closed = "closed"
    damaged = "damaged"
    vandalized = "vandalized"
    other = "other"


class ReportStatus(str, enum.Enum):
    active = "active"
    resolved = "resolved"
    expired = "expired"
    dismissed = "dismissed"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    poi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pois.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(
        Enum(ReportType, name="report_type_enum", create_constraint=True),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(ReportStatus, name="report_status_enum", create_constraint=True),
        nullable=False,
        default=ReportStatus.active,
        server_default=text("'active'"),
    )
    confirmation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_reports_poi_status", "poi_id", "status"),
        # Partial index — used by the 15-minute auto-expiry sweep
        Index(
            "ix_reports_active_expires_at",
            "expires_at",
            postgresql_where=text("status = 'active'"),
        ),
    )


class ReportConfirmation(Base):
    """Corroboration of a report. One row per (report, user)."""

    __tablename__ = "report_confirmations"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "report_id", "user_id", name="pk_report_confirmations"
        ),
    )
