from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from src.database.config import sqlalchemy_config
from src.transcription.services import TranscriptionTaskService


async def provide_transcription_task_service() -> AsyncGenerator[TranscriptionTaskService, None]:
    async with TranscriptionTaskService.new(config=sqlalchemy_config) as service:
        yield service


type TranscriptionTaskServiceDep = Annotated[
    TranscriptionTaskService, Depends(provide_transcription_task_service)
]
