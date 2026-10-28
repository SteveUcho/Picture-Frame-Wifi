"""add scanOrientation column to models table

Revision ID: 2297843d37d9
Revises: 3b25e696438b
Create Date: 2026-10-27 22:54:18.249763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2297843d37d9'
down_revision: Union[str, Sequence[str], None] = '3b25e696438b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("models", sa.Column("scanOrientation", sa.String(255)))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("models", "scanOrientation")
