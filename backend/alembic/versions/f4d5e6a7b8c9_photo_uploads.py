"""photo_uploads + pois.photo_url

Phase 2.2.5: presigned upload bookkeeping table + a denormalised
``photo_url`` column on the POI for the canonical R2 path of the
claimed photo.

Revision ID: f4d5e6a7b8c9
Revises: e3c4d5f6a7b8
Create Date: 2026-05-02 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "f4d5e6a7b8c9"
down_revision: Union[str, None] = "e3c4d5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PHOTO_UPLOAD_STATUS = sa.Enum(
    "pending",
    "claimed",
    "deleted",
    name="photo_upload_status_enum",
    create_constraint=True,
)


def upgrade() -> None:
    PHOTO_UPLOAD_STATUS.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "photo_uploads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            PHOTO_UPLOAD_STATUS,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "claimed_by_poi_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pois.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index(
        "ix_photo_uploads_user_id", "photo_uploads", ["user_id"]
    )
    op.create_index(
        "ix_photo_uploads_status", "photo_uploads", ["status"]
    )
    op.create_index(
        "ix_photo_uploads_expires_at", "photo_uploads", ["expires_at"]
    )
    op.create_index(
        "ix_photo_uploads_claimed_by_poi_id",
        "photo_uploads",
        ["claimed_by_poi_id"],
    )

    op.add_column(
        "pois",
        sa.Column("photo_url", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pois", "photo_url")
    op.drop_index("ix_photo_uploads_claimed_by_poi_id", table_name="photo_uploads")
    op.drop_index("ix_photo_uploads_expires_at", table_name="photo_uploads")
    op.drop_index("ix_photo_uploads_status", table_name="photo_uploads")
    op.drop_index("ix_photo_uploads_user_id", table_name="photo_uploads")
    op.drop_table("photo_uploads")
    PHOTO_UPLOAD_STATUS.drop(op.get_bind(), checkfirst=True)
