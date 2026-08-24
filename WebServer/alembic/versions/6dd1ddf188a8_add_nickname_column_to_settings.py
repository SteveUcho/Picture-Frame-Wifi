"""add nickname column to settings

Revision ID: 6dd1ddf188a8
Revises: 047ed6fd9e1c
Create Date: 2026-08-23 23:26:46.946215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dd1ddf188a8'
down_revision: Union[str, Sequence[str], None] = '047ed6fd9e1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("settings", sa.Column("name", sa.String(255)))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("settings", "name")
