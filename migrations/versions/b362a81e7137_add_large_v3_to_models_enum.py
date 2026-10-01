"""add large-v3 to models enum

Revision ID: b362a81e7137
Revises: 37d44461c844
Create Date: 2026-10-01 15:44:59.590101

"""
from typing import Sequence, Union

import advanced_alchemy
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b362a81e7137'
down_revision: Union[str, Sequence[str], None] = '37d44461c844'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute(f"ALTER TYPE transcription_model ADD VALUE IF NOT EXISTS 'LARGE_V3'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
