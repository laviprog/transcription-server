from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from transcription_server.core.config import settings
from transcription_server.worker.transcription import SpeechTranscriber

if TYPE_CHECKING:
    from transcription_server.domain.transcription.enums import Model

_TRANSCRIBER: SpeechTranscriber | None = None
_LOCK = threading.Lock()


def get_transcriber(
    *,
    preload: list[Model] | None = None,
) -> SpeechTranscriber:
    global _TRANSCRIBER
    if _TRANSCRIBER is None:
        with _LOCK:
            if _TRANSCRIBER is None:
                _TRANSCRIBER = SpeechTranscriber(
                    device=settings.DEVICE,
                    compute_type=settings.COMPUTE_TYPE,
                    download_root=settings.DOWNLOAD_ROOT,
                    init_asr_models=list(preload or []),
                    batch_size=settings.BATCH_SIZE,
                    chunk_size=settings.CHUNK_SIZE,
                    hf_token=settings.HF_TOKEN,
                )
    return _TRANSCRIBER


def cleanup_transcriber():
    global _TRANSCRIBER
    with _LOCK:
        if _TRANSCRIBER is not None:
            try:
                _TRANSCRIBER.clean()
            finally:
                _TRANSCRIBER = None
