"""poi_verification_status

Phase 2.2.4: add ``verification_status`` enum to ``pois`` so we can
distinguish user-submitted POIs that haven't been confirmed yet.

Revision ID: e3c4d5f6a7b8
Revises: d2b3c4e5f6a7
Create Date: 2026-05-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e3c4d5f6a7b8"
down_revision: Union[str, None] = "d2b3c4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VERIFICATION_STATUS = sa.Enum(
    "unverified",
    "verified",
    name="poi_verification_status_enum",
    create_constraint=True,
)


def upgrade() -> None:
    # Pre-create the enum so we can use it in alter_column with explicit
    # server_default.
    VERIFICATION_STATUS.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "pois",
        sa.Column(
            "verification_status",
            VERIFICATION_STATUS,
            nullable=False,
            # Existing rows are imported / seed → treat as verified
            server_default=sa.text("'verified'"),
        ),
    )
    op.create_index(
        "ix_pois_verification_status",
        "pois",
        ["verification_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_pois_verification_status", table_name="pois")
    op.drop_column("pois", "verification_status")
    VERIFICATION_STATUS.drop(op.get_bind(), checkfirst=True)
