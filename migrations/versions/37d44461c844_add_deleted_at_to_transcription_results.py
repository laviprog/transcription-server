"""add deleted_at to transcription_results

Revision ID: 37d44461c844
Revises: 2a972f8b9037
Create Date: 2026-09-29 17:24:40.817203

"""
from typing import Sequence, Union

import advanced_alchemy
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37d44461c844'
down_revision: Union[str, Sequence[str], None] = '2a972f8b9037'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transcription_results",
        sa.Column(
            "deleted_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("transcription_results", "deleted_at")
