"""Append-only reputation ledger (Phase 4.2.1).

Each row is an immutable event. The user's running ``reputation`` column
is the sum of all their event deltas (recomputed nightly to fix drift).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ReputationEventType(str, enum.Enum):
    poi_submitted_verified = "poi_submitted_verified"  # +5
    poi_submitted_rejected = "poi_submitted_rejected"  # -3
    confirmation = "confirmation"  # +1 to submitter
    report_submitted_resolved = "report_submitted_resolved"  # +2 to reporter
    report_dismissed_admin = "report_dismissed_admin"  # -5 to reporter
    daily_active = "daily_active"  # +0


# Canonical deltas — kept here so service code never hard-codes them.
EVENT_DELTAS: dict[ReputationEventType, int] = {
    ReputationEventType.poi_submitted_verified: 5,
    ReputationEventType.poi_submitted_rejected: -3,
    ReputationEventType.confirmation: 1,
    ReputationEventType.report_submitted_resolved: 2,
    ReputationEventType.report_dismissed_admin: -5,
    ReputationEventType.daily_active: 0,
}


class ReputationEvent(Base):
    __tablename__ = "reputation_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        Enum(
            ReputationEventType,
            name="reputation_event_type_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    # Loose reference (POI id, report id, …); validated by the caller.
    ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_reputation_events_user_id", "user_id"),
        Index("ix_reputation_events_user_created", "user_id", "created_at"),
    )
