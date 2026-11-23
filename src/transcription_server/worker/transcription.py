from __future__ import annotations

import gc
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, cast

import structlog
import torch
from whisperx.alignment import (
    DEFAULT_ALIGN_MODELS_HF,
    DEFAULT_ALIGN_MODELS_TORCH,
    align,
    load_align_model,
)
from whisperx.asr import FasterWhisperPipeline, load_model
from whisperx.audio import load_audio
from whisperx.diarize import DiarizationPipeline, assign_word_speakers
from whisperx.schema import AlignedTranscriptionResult, SingleSegment, TranscriptionResult

from transcription_server.core.utils import retry

log = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from numpy import ndarray
    from pandas import DataFrame
    from transformers import Wav2Vec2ForCTC

    from transcription_server.worker.schema import Segment


class SpeechTranscriber:
    """
    Handles speech transcription, alignment, and speaker diarization using WhisperX.
    """

    def __init__(
        self,
        device: str,
        compute_type: str,
        download_root: str,
        batch_size: int,
        chunk_size: int,
        max_align_models: int = 2,
        hf_token: str | None = None,
    ):
        """
        Initializes the SpeechTranscription with device configuration
        and optional models to preload.

        :param device: Device to use for inference ("cpu" or "cuda").
        :param compute_type: Compute type for inference (e.g., "float16", "int8").
        :param download_root: Directory for downloading and caching models.
        :param batch_size: Batch size for inference.
        :param chunk_size: Chunk size (in seconds) for audio splitting.
        :param max_align_models: Maximum number of alignment models kept in memory.
        :param hf_token: Optional Hugging Face token for private diarization model access.
        """
        self.__asr_models_cache: dict[str, FasterWhisperPipeline] = {}
        self.__alignment_models_cache: OrderedDict[str, tuple[Wav2Vec2ForCTC, dict[str, Any]]] = (
            OrderedDict()
        )
        self.__diarization_model: DiarizationPipeline | None = None

        self._device = device
        self._compute_type = compute_type
        self._download_root = download_root
        self._batch_size = batch_size
        self._chunk_size = chunk_size
        self._max_align_models = max_align_models
        self._hf_token = hf_token

    def preload_models(
        self, asr_models: list[str] | None = None, align_models: list[str] | None = None
    ) -> None:
        """
        Preload models into cache.

        :param asr_models: List of ASR model names to preload.
        :param align_models: List of language codes for alignment models to preload.
        """
        for model in asr_models or []:
            self._load_asr_model(model)
        for lang_code in align_models or []:
            self._load_alignment_model(lang_code)

    def _load_asr_model(self, model_name: str) -> None:
        """
        Loads an ASR model and stores it in the cache.
        """
        log.info("Loading ASR model", model_name=model_name)
        try:
            self.__asr_models_cache[model_name] = load_model(
                whisper_arch=model_name,
                device=self._device,
                compute_type=self._compute_type,
                download_root=self._download_root,
            )
            log.info("ASR model loaded", model_name=model_name)
        except Exception as e:
            log.error("Failed to load ASR model", model_name=model_name, error=str(e))
            raise e

    def _load_alignment_model(self, lang_code: str) -> None:
        """
        Loads an alignment model and stores it in the cache.
        """
        self._evict_alignment_models(keep=self._max_align_models - 1)
        log.info("Loading alignment model", lang_code=lang_code)
        try:
            self.__alignment_models_cache[lang_code] = load_align_model(
                language_code=lang_code,
                device=self._device,
                model_dir=self._download_root,
            )
            log.info("Alignment model loaded", lang_code=lang_code)
        except Exception as e:
            log.error("Failed to load alignment model", lang_code=lang_code, error=str(e))
            raise e

    def _evict_alignment_models(self, keep: int) -> None:
        evicted = False
        while len(self.__alignment_models_cache) > keep:
            lang_code, _ = self.__alignment_models_cache.popitem(last=False)
            log.info("Evicted align model", lang_code=lang_code)
            evicted = True
        if evicted:
            gc.collect()
            self._clean_cuda()

    def _load_diarization_model(self, model_name: str | None = None) -> None:
        """
        Loads a diarization model and stores it in the cache.
        """
        log.info("Loading diarization model...", model_name=model_name)
        try:
            self.__diarization_model = DiarizationPipeline(
                model_name=model_name,
                token=self._hf_token,
                device=self._device,
                cache_dir=self._download_root,
            )
            log.info("Diarization model loaded", model_name=model_name)
        except Exception as e:
            log.error("Failed to load diarization model", model_name=model_name, error=str(e))
            raise e

    def _get_asr_model(self, model_name: str) -> FasterWhisperPipeline:
        """
        Retrieves the ASR model from cache or loads it if not present.
        """
        if model_name not in self.__asr_models_cache:
            self._load_asr_model(model_name=model_name)
        return self.__asr_models_cache[model_name]

    def _get_alignment_model(self, lang_code: str) -> tuple[Wav2Vec2ForCTC, dict[str, Any]]:
        """
        Retrieves the alignment model for the specified language code from cache or loads it
        if not present.
        """
        if lang_code not in self.__alignment_models_cache:
            self._load_alignment_model(lang_code=lang_code)
        self.__alignment_models_cache.move_to_end(lang_code)
        return self.__alignment_models_cache[lang_code]

    def _get_diarization_model(self, model_name: str | None = None) -> DiarizationPipeline:
        """
        Retrieves the diarization model from cache or loads it if not present.
        """
        if self.__diarization_model is None:
            self._load_diarization_model(model_name=model_name)
        return cast("DiarizationPipeline", self.__diarization_model)

    @staticmethod
    def _load_audio(audio_file: str) -> ndarray:
        """
        Loads audio file into a numpy array.
        """
        log.debug("Loading audio file", audio_file=audio_file)
        try:
            audio = load_audio(file=audio_file)
            log.debug("Loaded audio file", audio_file=audio_file)
        except RuntimeError as e:
            log.error("Failed to load audio file", audio_file=audio_file, error=str(e))
            raise e
        return audio

    @retry()
    def _transcribe(
        self,
        audio: ndarray,
        audio_file: str,
        model: str,
        language: str | None = None,
    ) -> TranscriptionResult:
        """
        Transcribes the given audio using the specified ASR model and language.
        """
        asr = self._get_asr_model(model_name=model)

        log.debug(
            "Transcribing...",
            model=model,
            language=language,
            batch_size=self._batch_size,
            chunk_size=self._chunk_size,
        )
        try:
            result = asr.transcribe(
                audio=audio,
                language=language,
                batch_size=self._batch_size,
                chunk_size=self._chunk_size,
            )
            log.debug("Transcribed audio file", audio_file=audio_file)
        except RuntimeError as e:
            log.error("Transcription runtime error", audio_file=audio_file, error=str(e))
            self.clean()
            raise e
        except Exception as e:
            log.error("Transcribing failed", audio_file=audio_file, error=str(e))
            raise e

        return result

    @retry()
    def _align(
        self, segments: list[SingleSegment], audio: ndarray, language: str
    ) -> AlignedTranscriptionResult | None:
        """
        Align the transcription segments with the audio using the alignment model.
        """
        if language not in DEFAULT_ALIGN_MODELS_TORCH and language not in DEFAULT_ALIGN_MODELS_HF:
            log.info("No align model for language, skipping alignment", language=language)
            return None
        try:
            align_model, metadata = self._get_alignment_model(language)
            return align(
                segments,
                align_model,
                metadata,
                audio,
                device=self._device,
            )
        except RuntimeError as e:
            log.warning("Alignment failed", error=str(e))
            self.clean()
            raise e
        except Exception as e:
            log.warning("Alignment failed (fallback to raw segments)", error=str(e))
            return None

    @retry()
    def _diarize(
        self,
        transcription_result: TranscriptionResult,
        audio: ndarray,
        num_speakers: int | None = None,
    ) -> TranscriptionResult:
        """
        Performs speaker diarization and assigns speakers to transcription segments.
        """
        diarization_model = self._get_diarization_model()
        log.debug(
            "Running diarization pipeline",
            num_speakers=num_speakers,
        )
        try:
            diarization_result = diarization_model(audio, num_speakers=num_speakers)
            diarization_segments: DataFrame = (
                diarization_result[0]
                if isinstance(diarization_result, tuple)
                else diarization_result
            )
            return cast(
                "TranscriptionResult",
                assign_word_speakers(diarization_segments, transcription_result),
            )
        except RuntimeError as e:
            log.warning("Diarization failed", error=str(e))
            self.clean()
            raise e
        except Exception as e:
            log.warning("Diarization failed", error=str(e))
            raise

    def transcribe(
        self,
        audio_file: str,
        model: str,
        language: str | None,
        recognition_mode: bool,
        num_speakers: int | None,
        align_mode: bool,
    ) -> list[Segment]:
        """
        Transcribes the given audio file, optionally performing speaker diarization.
        """
        audio = self._load_audio(audio_file)

        transcription_result = self._transcribe(
            audio=audio,
            audio_file=audio_file,
            model=model,
            language=language,
        )

        if align_mode:
            align_result = self._align(
                segments=transcription_result["segments"],
                audio=audio,
                language=transcription_result["language"],
            )

            if align_result:
                transcription_result["segments"] = [
                    SingleSegment(start=seg["start"], end=seg["end"], text=seg["text"].strip())
                    for seg in align_result["segments"]
                ]

        if recognition_mode:
            transcription_result = self._diarize(transcription_result, audio, num_speakers)

        return cast("list[Segment]", transcription_result["segments"])

    def _clean_cuda(self) -> None:
        """
        Cleans up CUDA memory if using GPU.
        """
        if self._device.startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def clean(self) -> None:
        """
        Cleans up cached models and frees memory.
        """
        log.debug("Cleaning up resources...")
        self.__asr_models_cache.clear()
        self.__alignment_models_cache.clear()
        self.__diarization_model = None
        gc.collect()
        self._clean_cuda()
        log.debug("Cleanup complete")
