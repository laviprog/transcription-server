from celery.exceptions import SoftTimeLimitExceeded

from src.config import settings

from .app import celery_app
from .hooks import DBReportingTask


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
    from ..transcription.enums import Language, Model
    from .state import get_transcriber

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
            "speaker": int(segment["speaker"].split("_")[-1]) + 1
            if segment.get("speaker", None)
            else None,
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
