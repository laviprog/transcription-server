from datetime import UTC, datetime
from uuid import UUID

import structlog
from celery import Task, states
from sqlalchemy import func

from transcription_server.core.utils import remove_file
from transcription_server.domain.transcription.models import Status, TranscriptionTaskModel
from transcription_server.worker.db import complete_task_sync, update_task_sync

log = structlog.get_logger(__name__)


class DBReportingTask(Task):
    """
    Mirrors the Celery task lifecycle into the transcription_tasks table and
    guarantees the uploaded audio file is removed once the task is done.
    """

    @staticmethod
    def _mark_failed(task_id: str, message: str) -> None:
        try:
            update_task_sync(
                UUID(task_id),
                status=Status.FAILED,
                completed_at=datetime.now(UTC),
                message=message,
            )
        except Exception as e:
            log.error("Failed to mark task as FAILED", task_id=task_id, error=str(e))

    def before_start(self, task_id, args, kwargs):
        try:
            update_task_sync(
                UUID(task_id),
                status=Status.IN_PROGRESS,
                # Keep the timestamp of the first attempt across retries.
                started_at=func.coalesce(TranscriptionTaskModel.started_at, datetime.now(UTC)),
                message="Processing transcription...",
            )
        except Exception as e:
            log.error("before_start update failed", task_id=task_id, error=str(e))

    def on_success(self, retval, task_id, args, kwargs):
        transcription_result = retval.get("result") if isinstance(retval, dict) else None

        if transcription_result is None:
            log.error(
                "Unexpected retval format in on_success",
                task_id=task_id,
                retval_type=type(retval).__name__,
            )
            self._mark_failed(task_id, "Transcription produced no result")
            return

        try:
            complete_task_sync(
                UUID(task_id),
                transcription_result=transcription_result,
                completed_at=datetime.now(UTC),
                message="Completed successfully",
            )
            log.debug("Transcription result saved", task_id=task_id)
        except Exception as e:
            log.error("Failed to persist transcription result", task_id=task_id, error=str(e))
            self._mark_failed(task_id, f"Failed to persist transcription result: {e}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        retries = self.request.retries + 1
        log.warning(
            "Task retry scheduled",
            task_id=task_id,
            retries=retries,
            max_retries=self.max_retries,
            error=str(exc),
        )
        try:
            update_task_sync(
                UUID(task_id),
                status=Status.IN_PROGRESS,
                message=f"Retrying after error (attempt {retries}/{self.max_retries}): {exc}",
            )
        except Exception as e:
            log.error("on_retry update failed", task_id=task_id, error=str(e))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self._mark_failed(task_id, str(exc) or "Failed transcription")

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if status in {states.RETRY, states.REJECTED}:
            return

        audio_file = (kwargs or {}).get("audio_file")
        if audio_file:
            remove_file(audio_file)
            log.debug("Temporary audio file removed", task_id=task_id, audio_file=audio_file)
