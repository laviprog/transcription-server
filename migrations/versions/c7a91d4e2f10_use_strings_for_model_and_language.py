"""use strings for model and language

Revision ID: c7a91d4e2f10
Revises: b362a81e7137
Create Date: 2026-11-23 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c7a91d4e2f10"
down_revision: Union[str, Sequence[str], None] = "b362a81e7137"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MODEL_LABELS = ["SMALL", "TURBO", "LARGE_V3_TURBO", "LARGE_V3"]
LANGUAGE_LABELS = [
    "RU",
    "EN",
    "DE",
    "FR",
    "ES",
    "IT",
    "PT",
    "ZH",
    "JA",
    "KO",
    "UK",
    "AR",
    "HY",
    "KA",
]


def upgrade() -> None:
    op.alter_column(
        "transcription_tasks",
        "model",
        existing_type=postgresql.ENUM(name="transcription_model"),
        type_=sa.String(),
        postgresql_using="model::text",
        existing_nullable=False,
    )
    op.alter_column(
        "transcription_tasks",
        "language",
        existing_type=postgresql.ENUM(name="transcription_language"),
        type_=sa.String(),
        postgresql_using="language::text",
        existing_nullable=True,
    )
    op.execute("DROP TYPE transcription_model")
    op.execute("DROP TYPE transcription_language")


def downgrade() -> None:
    bind = op.get_bind()
    invalid_models = (
        bind.execute(
            sa.text(
                "SELECT DISTINCT model FROM transcription_tasks WHERE model NOT IN :labels"
            ).bindparams(sa.bindparam("labels", expanding=True)),
            {"labels": MODEL_LABELS},
        )
        .scalars()
        .all()
    )
    invalid_languages = (
        bind.execute(
            sa.text(
                "SELECT DISTINCT language FROM transcription_tasks "
                "WHERE language IS NOT NULL AND language NOT IN :labels"
            ).bindparams(sa.bindparam("labels", expanding=True)),
            {"labels": LANGUAGE_LABELS},
        )
        .scalars()
        .all()
    )
    if invalid_models or invalid_languages:
        raise RuntimeError(
            "Cannot restore enum columns with unsupported values: "
            f"models={invalid_models}, languages={invalid_languages}"
        )

    model_enum = postgresql.ENUM(*MODEL_LABELS, name="transcription_model")
    language_enum = postgresql.ENUM(*LANGUAGE_LABELS, name="transcription_language")
    model_enum.create(bind)
    language_enum.create(bind)
    op.alter_column(
        "transcription_tasks",
        "model",
        existing_type=sa.String(),
        type_=model_enum,
        postgresql_using="model::transcription_model",
        existing_nullable=False,
    )
    op.alter_column(
        "transcription_tasks",
        "language",
        existing_type=sa.String(),
        type_=language_enum,
        postgresql_using="language::transcription_language",
        existing_nullable=True,
    )
