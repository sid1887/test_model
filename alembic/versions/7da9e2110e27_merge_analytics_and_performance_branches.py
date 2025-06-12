"""Merge analytics and performance branches

Revision ID: 7da9e2110e27
Revises: 1095e55c3163, add_analytics_tables
Create Date: 2025-06-11 21:36:23.155207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7da9e2110e27'
down_revision: Union[str, None] = ('1095e55c3163', 'add_analytics_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
