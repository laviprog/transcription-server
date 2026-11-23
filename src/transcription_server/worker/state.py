from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from transcription_server.core.config import settings
from transcription_server.domain.transcription.enums import Language
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
                transcriber = SpeechTranscriber(
                    device=settings.DEVICE,
                    compute_type=settings.COMPUTE_TYPE,
                    download_root=settings.DOWNLOAD_ROOT,
                    batch_size=settings.BATCH_SIZE,
                    chunk_size=settings.CHUNK_SIZE,
                    max_align_models=settings.MAX_ALIGN_MODELS,
                    hf_token=settings.HF_TOKEN,
                )
                transcriber.preload_models(
                    asr_models=[model.value for model in preload or []],
                    align_models=[Language.RU.value, Language.EN.value],
                )
                _TRANSCRIBER = transcriber
    return _TRANSCRIBER


def cleanup_transcriber():
    global _TRANSCRIBER
    with _LOCK:
        if _TRANSCRIBER is not None:
            try:
                _TRANSCRIBER.clean()
            finally:
                _TRANSCRIBER = None
