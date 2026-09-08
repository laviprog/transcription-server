from contextlib import suppress
from uuid import UUID

from advanced_alchemy.extensions.fastapi import service
from fastapi import HTTPException, UploadFile, status

from .. import log
from ..utils.files import save_upload_to_temp
from ..utils.media import get_duration_seconds, get_filesize_bytes
from ..workers.app import celery_app
from .enums import Language, Model
from .models import Status, TranscriptionTaskModel
from .repositories import TranscriptionResultRepository, TranscriptionTaskRepository
from .schemas import TranscriptionTask, TranscriptionTaskWithResult


class TranscriptionTaskService(
    service.SQLAlchemyAsyncRepositoryService[TranscriptionTaskModel, TranscriptionTaskRepository]
):
    """Transcription Task Service"""

    repository_type = TranscriptionTaskRepository

    def __init__(self, session, **kwargs):
        kwargs.setdefault("auto_commit", True)
        super().__init__(session=session, **kwargs)
        self.result_repository = TranscriptionResultRepository(session=session)

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
        except ValueError as e:
            with suppress(Exception):
                await file.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid audio file",
            ) from e
        else:
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

        transcription_task_model = await self.create(transcription_task_model)

        celery_app.send_task(
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
        )

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
