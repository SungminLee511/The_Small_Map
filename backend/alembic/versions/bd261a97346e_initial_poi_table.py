"""initial_poi_table

Revision ID: bd261a97346e
Revises:
Create Date: 2026-04-25 15:42:26.064275
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bd261a97346e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('pois',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('poi_type', sa.Enum('toilet', 'trash_can', 'bench', 'smoking_area', 'water_fountain', name='poi_type_enum', create_constraint=True), nullable=False),
    sa.Column('location', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeogFromText', name='geography', nullable=False), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('source', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('active', 'removed', name='poi_status_enum', create_constraint=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pois_location', 'pois', ['location'], unique=False, postgresql_using='gist')
    op.create_index('ix_pois_type_status', 'pois', ['poi_type', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_pois_type_status', table_name='pois')
    op.drop_index('ix_pois_location', table_name='pois', postgresql_using='gist')
    op.drop_table('pois')
