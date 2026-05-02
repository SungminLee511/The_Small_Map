"""reputation_events ledger + removal_proposals

Phase 4.2.1 + 4.2.4.

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-05-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REPUTATION_EVENT_TYPE = sa.Enum(
    "poi_submitted_verified",
    "poi_submitted_rejected",
    "confirmation",
    "report_submitted_resolved",
    "report_dismissed_admin",
    "daily_active",
    name="reputation_event_type_enum",
    create_constraint=True,
)


def upgrade() -> None:
    REPUTATION_EVENT_TYPE.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "reputation_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", REPUTATION_EVENT_TYPE, nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("ref_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_reputation_events_user_id", "reputation_events", ["user_id"]
    )
    op.create_index(
        "ix_reputation_events_user_created",
        "reputation_events",
        ["user_id", "created_at"],
    )

    # Removal proposals (Phase 4.2.4) — separate table keeps the reports
    # workflow clean and avoids growing the report_type enum.
    op.create_table(
        "poi_removal_proposals",
        sa.Column(
            "poi_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pois.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint(
            "poi_id", "user_id", name="pk_poi_removal_proposals"
        ),
    )
    op.create_index(
        "ix_poi_removal_proposals_poi_id",
        "poi_removal_proposals",
        ["poi_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_poi_removal_proposals_poi_id", table_name="poi_removal_proposals"
    )
    op.drop_table("poi_removal_proposals")
    op.drop_index(
        "ix_reputation_events_user_created", table_name="reputation_events"
    )
    op.drop_index(
        "ix_reputation_events_user_id", table_name="reputation_events"
    )
    op.drop_table("reputation_events")
    REPUTATION_EVENT_TYPE.drop(op.get_bind(), checkfirst=True)
