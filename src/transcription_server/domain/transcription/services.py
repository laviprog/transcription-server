import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

import structlog
from advanced_alchemy.extensions.fastapi import service
from fastapi import HTTPException, UploadFile, status

from transcription_server.api.transcriptions.schemas import (
    TranscriptionTask,
    TranscriptionTaskWithResult,
)
from transcription_server.api.utils import (
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    save_upload_to_temp,
)
from transcription_server.core.utils import (
    get_duration_seconds,
    get_filesize_bytes,
    remove_file_async,
)
from transcription_server.domain.transcription.enums import Language, Model
from transcription_server.domain.transcription.models import Status, TranscriptionTaskModel
from transcription_server.domain.transcription.repositories import TranscriptionTaskRepository
from transcription_server.worker.app import celery_app

log = structlog.get_logger(__name__)


class TranscriptionTaskService(
    service.SQLAlchemyAsyncRepositoryService[TranscriptionTaskModel, TranscriptionTaskRepository]
):
    """Transcription Task Service"""

    repository_type = TranscriptionTaskRepository

    def __init__(self, session, **kwargs):
        kwargs.setdefault("auto_commit", True)
        super().__init__(session=session, **kwargs)

    async def create_transcription_task(
        self,
        api_key_id: UUID,
        file: UploadFile,
        model: Model,
        language: Language | None,
        recognition_mode: bool,
        num_speakers: int | None,
        align_mode: bool,
    ) -> TranscriptionTask:
        try:
            audio_path = await save_upload_to_temp(file)
        except FileTooLargeError as e:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=str(e),
            ) from e
        except (UnsupportedFileTypeError, EmptyFileError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        except Exception as e:
            log.error("Failed to store uploaded file", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store uploaded file",
            ) from e
        finally:
            with suppress(Exception):
                await file.close()
        try:
            duration_seconds = get_duration_seconds(audio_path)
        except Exception as e:
            log.error("Failed to get audio duration", path=audio_path, error=str(e))
            duration_seconds = None
        try:
            file_size_bytes = get_filesize_bytes(audio_path)
        except Exception as e:
            log.error("Failed to get file size", path=audio_path, error=str(e))
            file_size_bytes = None

        transcription_task_model = TranscriptionTaskModel(
            api_key_id=api_key_id,
            status=Status.PENDING,
            model=model,
            language=language,
            align_mode=align_mode,
            recognition_mode=recognition_mode,
            num_speakers=num_speakers,
            message="Task created and queued for processing.",
            duration_seconds=duration_seconds,
            file_size_bytes=file_size_bytes,
        )

        try:
            transcription_task_model = await self.create(transcription_task_model)
        except Exception as e:
            log.error("Failed to create transcription task row", error=str(e))
            await remove_file_async(audio_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create transcription task",
            ) from e

        try:
            await asyncio.to_thread(
                celery_app.send_task,
                "transcribe_audio",
                task_id=str(transcription_task_model.id),
                kwargs={
                    "audio_file": audio_path,
                    "model": model.value,
                    "language": language.value if language else None,
                    "recognition_mode": recognition_mode,
                    "num_speakers": num_speakers,
                    "align_mode": align_mode,
                },
                retry=True,
                retry_policy={
                    "max_retries": 3,
                    "interval_start": 0,
                    "interval_step": 0.2,
                    "interval_max": 1,
                },
            )
        except Exception as e:
            log.error(
                "Failed to enqueue transcription task",
                task_id=str(transcription_task_model.id),
                error=str(e),
            )
            await remove_file_async(audio_path)
            with suppress(Exception):
                transcription_task_model.status = Status.FAILED
                transcription_task_model.message = "Failed to enqueue transcription task"
                transcription_task_model.completed_at = datetime.now(UTC)
                await self.update(transcription_task_model)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Transcription service is temporarily unavailable, please retry later",
            ) from e

        return TranscriptionTask(
            task_id=transcription_task_model.id,
            status=transcription_task_model.status,
            created_at=transcription_task_model.created_at,
            message=transcription_task_model.message,
        )

    async def get_transcription_task(
        self,
        task_id: str,
        api_key_id: UUID,
    ) -> TranscriptionTaskWithResult:
        try:
            task_uuid = UUID(task_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid task id",
            ) from e

        transcription_task = await self.repository.get_with_result(task_uuid)

        if not transcription_task or transcription_task.api_key_id != api_key_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription task not found",
            )

        return TranscriptionTaskWithResult.from_model(transcription_task)
