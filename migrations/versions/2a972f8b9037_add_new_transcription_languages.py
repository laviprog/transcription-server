"""add new transcription languages

Revision ID: 2a972f8b9037
Revises: 4d75b008ff3e
Create Date: 2026-09-29 15:49:42.701971

"""
from typing import Sequence, Union

import advanced_alchemy
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a972f8b9037'
down_revision: Union[str, Sequence[str], None] = '4d75b008ff3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_LANGUAGES = ["DE", "FR", "ES", "IT", "PT", "ZH", "JA", "KO", "UK", "AR", "HY", "KA"]

def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        for lang in NEW_LANGUAGES:
            op.execute(f"ALTER TYPE transcription_language ADD VALUE IF NOT EXISTS '{lang}'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
