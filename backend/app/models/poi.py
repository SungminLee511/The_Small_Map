import enum
import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class POIType(str, enum.Enum):
    toilet = "toilet"
    trash_can = "trash_can"
    bench = "bench"
    smoking_area = "smoking_area"
    water_fountain = "water_fountain"


class POIStatus(str, enum.Enum):
    active = "active"
    removed = "removed"


class POIVerificationStatus(str, enum.Enum):
    unverified = "unverified"
    verified = "verified"


class POI(Base):
    __tablename__ = "pois"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    poi_type: Mapped[str] = mapped_column(
        Enum(POIType, name="poi_type_enum", create_constraint=True), nullable=False
    )
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    source: Mapped[str] = mapped_column(String(255), nullable=False, default="seed")
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    status: Mapped[str] = mapped_column(
        Enum(POIStatus, name="poi_status_enum", create_constraint=True),
        nullable=False,
        default=POIStatus.active,
    )
    verification_status: Mapped[str] = mapped_column(
        Enum(
            POIVerificationStatus,
            name="poi_verification_status_enum",
            create_constraint=True,
        ),
        nullable=False,
        default=POIVerificationStatus.verified,
        server_default=text("'verified'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_pois_location", "location", postgresql_using="gist"),
        Index("ix_pois_type_status", "poi_type", "status"),
        Index(
            "uq_pois_source_external_id",
            "source",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        Index("ix_pois_verification_status", "verification_status"),
    )
