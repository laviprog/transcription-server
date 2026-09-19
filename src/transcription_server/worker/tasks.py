from __future__ import annotations

from typing import TYPE_CHECKING

from celery.exceptions import SoftTimeLimitExceeded

from transcription_server.core.config import settings
from transcription_server.domain.transcription.enums import Language, Model
from transcription_server.worker.app import celery_app
from transcription_server.worker.hooks import DBReportingTask
from transcription_server.worker.state import get_transcriber

if TYPE_CHECKING:
    from .transcription import Segment


def _speaker_number(segment: Segment) -> int | None:
    """
    Turns a whisperx speaker label ("SPEAKER_00") into a 1-based speaker number.
    The key is absent when the segment was not diarized.
    """
    speaker = segment.get("speaker")
    return int(speaker.split("_")[-1]) + 1 if speaker else None


@celery_app.task(
    bind=True,
    name="transcribe_audio",
    base=DBReportingTask,
    autoretry_for=(Exception,),
    dont_autoretry_for=(SoftTimeLimitExceeded, ValueError, KeyError, FileNotFoundError),
    max_retries=settings.TASK_MAX_RETRIES,
    retry_backoff=settings.TASK_RETRY_BACKOFF,
    retry_backoff_max=settings.TASK_RETRY_BACKOFF_MAX,
    retry_jitter=True,
)
def transcribe_audio(
    self,
    *,
    audio_file: str,
    model: str,
    language: str | None,
    recognition_mode: bool,
    num_speakers: int | None,
    align_mode: bool,
) -> dict:

    transcriber = get_transcriber()

    segments = transcriber.transcribe(
        audio_file=audio_file,
        model=Model(model),
        language=Language(language) if language else None,
        recognition_mode=recognition_mode,
        num_speakers=num_speakers,
        align_mode=align_mode,
    )

    result = [
        {
            "number": i + 1,
            "content": segment["text"].strip(),
            "speaker": _speaker_number(segment),
            "start": segment["start"],
            "end": segment["end"],
        }
        for i, segment in enumerate(segments)
    ]

    # The audio file is removed in DBReportingTask.after_return so that it survives
    # retries and is cleaned up on failure too.
    return {
        "result": result,
    }
