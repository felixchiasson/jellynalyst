"""add genres to watch history

Revision ID: manual_1
Revises: 3a6d3e6e23c2
Create Date: 2024-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'manual_1'
down_revision: Union[str, None] = '3a6d3e6e23c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add genres column
    op.add_column('watch_history', sa.Column('genres', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    # Remove genres column
    op.drop_column('watch_history', 'genres')
