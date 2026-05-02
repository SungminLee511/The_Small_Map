"""phase1_poi_columns

Adds external_id, last_verified_at, verification_count, plus a partial unique
index on (source, external_id) for upsert idempotency.

Revision ID: c1a2b3d4e5f6
Revises: bd261a97346e
Create Date: 2026-05-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, None] = "bd261a97346e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pois",
        sa.Column("external_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "pois",
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "pois",
        sa.Column(
            "verification_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_index(
        "uq_pois_source_external_id",
        "pois",
        ["source", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_pois_source_external_id", table_name="pois")
    op.drop_column("pois", "verification_count")
    op.drop_column("pois", "last_verified_at")
    op.drop_column("pois", "external_id")
