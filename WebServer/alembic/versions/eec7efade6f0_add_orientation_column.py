"""add orientation column

Revision ID: eec7efade6f0
Revises:
Create Date: 2025-10-13 21:05:36.955700

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "eec7efade6f0"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("settings", sa.Column("orientation", sa.VARCHAR(255)))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("settings", "orientation")
