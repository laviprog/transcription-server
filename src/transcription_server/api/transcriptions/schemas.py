from datetime import datetime
from typing import Self
from uuid import UUID

from transcription_server.api.schemas import BaseSchema
from transcription_server.domain.transcription.models import Status, TranscriptionTaskModel


class ModelList(BaseSchema):
    models: list[str]


class LanguageList(BaseSchema):
    languages: list[str]


class TranscriptionSegment(BaseSchema):
    number: int
    content: str
    speaker: int | None = None
    start: float
    end: float


class TranscriptionTask(BaseSchema):
    task_id: UUID
    status: Status
    created_at: datetime
    message: str | None = None


class TranscriptionTaskWithResult(TranscriptionTask):
    result: list[TranscriptionSegment] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @classmethod
    def from_model(
        cls,
        model: TranscriptionTaskModel,
    ) -> Self:
        return cls(
            task_id=model.id,
            status=model.status,
            message=model.message,
            result=[
                TranscriptionSegment(
                    number=segment["number"],
                    content=segment["content"],
                    speaker=segment.get("speaker", None),
                    start=segment["start"],
                    end=segment["end"],
                )
                for segment in model.result.transcription_result
            ]
            if model.result
            else None,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )
