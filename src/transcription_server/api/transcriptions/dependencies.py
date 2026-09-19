from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from transcription_server.core.database.config import sqlalchemy_config
from transcription_server.domain.transcription.services import TranscriptionTaskService


async def provide_transcription_task_service() -> AsyncGenerator[TranscriptionTaskService, None]:
    async with TranscriptionTaskService.new(config=sqlalchemy_config) as service:
        yield service


type TranscriptionTaskServiceDep = Annotated[
    TranscriptionTaskService, Depends(provide_transcription_task_service)
]
