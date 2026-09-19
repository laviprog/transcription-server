from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .models import TranscriptionResultModel, TranscriptionTaskModel


class TranscriptionTaskRepository(SQLAlchemyAsyncRepository[TranscriptionTaskModel]):
    """Transcription task repository"""

    model_type = TranscriptionTaskModel

    async def get_with_result(self, task_id):
        """Get task with result eagerly loaded."""
        statement = (
            select(self.model_type)
            .where(self.model_type.id == task_id)
            .options(selectinload(self.model_type.result))
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class TranscriptionResultRepository(SQLAlchemyAsyncRepository[TranscriptionResultModel]):
    """Transcription result repository"""

    model_type = TranscriptionResultModel
