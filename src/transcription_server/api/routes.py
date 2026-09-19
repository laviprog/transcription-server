from fastapi import APIRouter, FastAPI

from transcription_server.api.schemas import HealthCheck
from transcription_server.api.transcriptions.routes import router as transcriptions_router

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
    app.include_router(router=transcriptions_router)
