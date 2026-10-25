"""guest_complaints

Revision ID: c8f2a6b1e4d9
Revises: 7f11edf3bbf1
Create Date: 2026-10-25 12:00:00.000000

Backward-compatible extension of `complaints` for guest (no-account) reports:
user_id becomes nullable and reporter/location/detail/photo columns are added.
Existing authenticated complaints are untouched (all new columns nullable).
"""
from alembic import op
import sqlalchemy as sa


revision = 'c8f2a6b1e4d9'
down_revision = '7f11edf3bbf1'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'complaints', 'user_id',
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column('complaints', sa.Column('reporter_name', sa.String(length=120), nullable=True))
    op.add_column('complaints', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('complaints', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('complaints', sa.Column('photo_path', sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column('complaints', 'photo_path')
    op.drop_column('complaints', 'description')
    op.drop_column('complaints', 'address')
    op.drop_column('complaints', 'reporter_name')
    op.alter_column(
        'complaints', 'user_id',
        existing_type=sa.Integer(),
        nullable=False,
    )
