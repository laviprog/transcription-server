from fastapi import APIRouter, FastAPI

from src.schemas import HealthCheck
from src.transcription.routes import router as speech_recognition_router

router = APIRouter(tags=["Monitoring"])


@router.get(
    "/healthcheck",
    responses={
        200: {
            "description": "Service is running",
        },
    },
)
async def healthcheck() -> HealthCheck:
    return HealthCheck()


def routes_register(app: FastAPI) -> None:
    app.include_router(router=router)
    app.include_router(router=speech_recognition_router)
