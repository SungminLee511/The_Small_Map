"""poi_confirmations

Phase 2.2.7: per-(poi,user) confirmation rows.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-05-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "b6c7d8e9f0a1"
down_revision: Union[str, None] = "a5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "poi_confirmations",
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
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("poi_id", "user_id", name="pk_poi_confirmations"),
    )
    op.create_index(
        "ix_poi_confirmations_user_id", "poi_confirmations", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_poi_confirmations_user_id", table_name="poi_confirmations")
    op.drop_table("poi_confirmations")
