"""poi_photo_processed_at

Phase 2.2.6: photo PIPA processing status. ``photo_processed_at`` is
``NULL`` until the background blur job completes; the frontend shows a
placeholder photo while it's null.

Revision ID: a5b6c7d8e9f0
Revises: f4d5e6a7b8c9
Create Date: 2026-05-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, None] = "f4d5e6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pois",
        sa.Column("photo_processed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pois", "photo_processed_at")
