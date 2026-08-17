"""create frame models table

Revision ID: 047ed6fd9e1c
Revises: eec7efade6f0
Create Date: 2026-08-16 20:48:20.510826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '047ed6fd9e1c'
down_revision: Union[str, Sequence[str], None] = 'eec7efade6f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'models',
        sa.Column('size', sa.Integer, primary_key=True),
        sa.Column('length', sa.Integer, nullable=False),
        sa.Column('width', sa.Integer, nullable=False),
    )
    op.add_column("settings", sa.Column("size", sa.Integer))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('settings', 'size')
    op.drop_table('models')
