"""POIConfirmation: an attestation that a POI exists (Phase 2.2.7).

One row per (poi, user). On insert we increment ``poi.verification_count``
and update ``poi.last_verified_at``. When the count crosses a threshold
the POI's ``verification_status`` flips to ``verified``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class POIConfirmation(Base):
    __tablename__ = "poi_confirmations"

    poi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pois.id", ondelete="CASCADE"),
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
        PrimaryKeyConstraint("poi_id", "user_id", name="pk_poi_confirmations"),
    )
