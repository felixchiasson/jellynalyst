"""Add constraint on jellyfin watch history table

Revision ID: add34408975a
Revises: a7b0dbbb14ee
Create Date: 2025-02-07 12:58:31.203989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add34408975a'
down_revision: Union[str, None] = 'a7b0dbbb14ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
