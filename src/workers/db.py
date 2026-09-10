from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.transcription.models import Status, TranscriptionResultModel, TranscriptionTaskModel
from src.workers import log

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session

_engine = None
_SessionLocal: sessionmaker | None = None


def init_db_sync() -> None:
    global _engine, _SessionLocal
    log.debug("Initializing sync DB engine")
    if _engine is None:
        _engine = create_engine(
            settings.DB_URL_SYNC,
            pool_pre_ping=True,
            future=True,
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
        log.debug("Sync DB sessionmaker created")


def dispose_db_sync() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None


@contextmanager
def _session_scope() -> Iterator[Session]:
    """Provides a session wrapped in a single transaction."""
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized: call init_db_sync() first")

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_task_sync(task_id: UUID, **values: Any) -> None:
    """
    Updates a transcription task row. Raises on failure.
    """
    with _session_scope() as session:
        session.execute(
            update(TranscriptionTaskModel)
            .where(TranscriptionTaskModel.id == task_id)
            .values(**values)
        )


def complete_task_sync(
    task_id: UUID,
    transcription_result: list[dict[str, Any]],
    completed_at: datetime,
    message: str,
) -> None:
    """
    Stores the transcription result and marks the task COMPLETED in one transaction.
    """
    with _session_scope() as session:
        existing_result = session.execute(
            select(TranscriptionResultModel).where(TranscriptionResultModel.task_id == task_id)
        ).scalar_one_or_none()

        if existing_result:
            log.debug("Updating existing transcription result", task_id=str(task_id))
            existing_result.transcription_result = transcription_result
        else:
            log.debug("Creating new transcription result", task_id=str(task_id))
            session.add(
                TranscriptionResultModel(task_id=task_id, transcription_result=transcription_result)
            )

        session.flush()

        session.execute(
            update(TranscriptionTaskModel)
            .where(TranscriptionTaskModel.id == task_id)
            .values(
                status=Status.COMPLETED,
                completed_at=completed_at,
                message=message,
            )
        )
