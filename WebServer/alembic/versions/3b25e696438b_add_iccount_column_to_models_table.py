"""add icCount column to models table

Revision ID: 3b25e696438b
Revises: 6dd1ddf188a8
Create Date: 2026-10-25 23:57:24.243576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b25e696438b'
down_revision: Union[str, Sequence[str], None] = '6dd1ddf188a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("models", sa.Column("icCount", sa.Integer, nullable=False, default=1))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("models", "icCount")
