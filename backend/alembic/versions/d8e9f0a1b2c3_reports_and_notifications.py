"""reports + report_confirmations + notifications

Phase 3.3.1 + 3.3.5.

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-05-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REPORT_TYPE = sa.Enum(
    "out_of_order",
    "overflowing",
    "dirty",
    "closed",
    "damaged",
    "vandalized",
    "other",
    name="report_type_enum",
    create_constraint=True,
)
REPORT_STATUS = sa.Enum(
    "active",
    "resolved",
    "expired",
    "dismissed",
    name="report_status_enum",
    create_constraint=True,
)
NOTIFICATION_TYPE = sa.Enum(
    "report_resolved",
    "report_expired",
    "poi_verified",
    name="notification_type_enum",
    create_constraint=True,
)


def upgrade() -> None:
    REPORT_TYPE.create(op.get_bind(), checkfirst=True)
    REPORT_STATUS.create(op.get_bind(), checkfirst=True)
    NOTIFICATION_TYPE.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "poi_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pois.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reporter_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("report_type", REPORT_TYPE, nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("photo_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "status",
            REPORT_STATUS,
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "confirmation_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolution_note", sa.String(length=500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_reports_poi_id", "reports", ["poi_id"])
    op.create_index("ix_reports_reporter_id", "reports", ["reporter_id"])
    op.create_index("ix_reports_poi_status", "reports", ["poi_id", "status"])
    op.create_index(
        "ix_reports_active_expires_at",
        "reports",
        ["expires_at"],
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "report_confirmations",
        sa.Column(
            "report_id",
            UUID(as_uuid=True),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint(
            "report_id", "user_id", name="pk_report_confirmations"
        ),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", NOTIFICATION_TYPE, nullable=False),
        sa.Column(
            "payload",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_notifications_user_unread", "notifications", ["user_id", "read_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("report_confirmations")
    op.drop_index("ix_reports_active_expires_at", table_name="reports")
    op.drop_index("ix_reports_poi_status", table_name="reports")
    op.drop_index("ix_reports_reporter_id", table_name="reports")
    op.drop_index("ix_reports_poi_id", table_name="reports")
    op.drop_table("reports")
    NOTIFICATION_TYPE.drop(op.get_bind(), checkfirst=True)
    REPORT_STATUS.drop(op.get_bind(), checkfirst=True)
    REPORT_TYPE.drop(op.get_bind(), checkfirst=True)
