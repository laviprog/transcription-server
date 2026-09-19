from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from transcription_server.api.security.dependencies import ApiKeyIdDep
from transcription_server.api.transcriptions.dependencies import TranscriptionTaskServiceDep
from transcription_server.api.transcriptions.schemas import (
    LanguageList,
    ModelList,
    TranscriptionTask,
    TranscriptionTaskWithResult,
)
from transcription_server.domain.transcription.enums import Language, Model

router = APIRouter(tags=["Speech Recognition"])


@router.get(
    "/models",
    summary="Get available models",
    description="Returns a list of available speech transcription models.",
    responses={
        200: {
            "description": "List of available models",
        },
    },
)
async def get_models() -> ModelList:
    return ModelList(models=Model.values())


@router.get(
    "/languages",
    summary="Get available languages",
    description="Returns a list of supported languages for transcription.",
    responses={
        200: {
            "description": "List of supported languages",
        },
    },
)
async def get_languages() -> LanguageList:
    return LanguageList(languages=Language.values())


@router.post(
    "/transcribe",
    summary="Transcribe Audio",
    description="""
        Transcribe audio into text.
    """,
    response_model_exclude_none=True,
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Transcription job created successfully",
            "model": TranscriptionTask,
        },
    },
)
async def transcribe(
    api_key_id: ApiKeyIdDep,
    transcription_task_service: TranscriptionTaskServiceDep,
    file: Annotated[UploadFile, File(..., description="Upload file (.mp3, .wav)")],
    language: Annotated[
        Language | None,
        Form(description="Language code for the audio (recommend, auto-detected if not provided)"),
    ] = None,
    model: Annotated[
        Model, Form(description="Transcription model to use (recommend turbo)")
    ] = Model.TURBO,
    recognition_mode: Annotated[bool, Form(description="Enable speaker detection")] = False,
    num_speakers: Annotated[
        int | None, Form(ge=1, le=15, description="Number of speakers for diarization")
    ] = None,
    align_mode: Annotated[bool, Form(description="Enable word-level timestamp alignment")] = False,
) -> TranscriptionTask:
    transcription_task = await transcription_task_service.create_transcription_task(
        api_key_id=api_key_id,
        file=file,
        language=language,
        model=model,
        recognition_mode=recognition_mode,
        num_speakers=num_speakers,
        align_mode=align_mode,
    )
    return transcription_task


@router.get(
    "/transcribe/{task_id}",
    summary="Get Transcription Task Status",
    description="Retrieve the status and result of a transcription task by its ID.",
    response_model_exclude_none=True,
    responses={
        status.HTTP_200_OK: {
            "description": "Transcription task retrieved successfully",
            "model": TranscriptionTaskWithResult,
        },
    },
)
async def get_transcription_task(
    task_id: str,
    api_key_id: ApiKeyIdDep,
    transcription_task_service: TranscriptionTaskServiceDep,
) -> TranscriptionTaskWithResult:
    transcription_task = await transcription_task_service.get_transcription_task(
        task_id, api_key_id
    )
    return transcription_task
