from fastapi import FastAPI
from scalar_fastapi import Theme, add_scalar_reference

from transcription_server.api.exceptions.handlers import setup_exception_handlers
from transcription_server.api.exceptions.responses import error_responses
from transcription_server.api.lifecycle import lifespan
from transcription_server.api.middlewares import register_middlewares
from transcription_server.api.routes import register_router
from transcription_server.core.config import settings
from transcription_server.core.log_config import configure as configure_logging

configure_logging("api")

app = FastAPI(
    title="Transcription Server API",
    version="0.0.1",
    root_path=settings.ROOT_PATH or "",
    responses=error_responses,
    lifespan=lifespan,
)

add_scalar_reference(
    app,
    route="/docs/scalar",
    theme=Theme.DEEP_SPACE,
    openapi_url=f"{settings.ROOT_PATH or ''}{app.openapi_url or '/openapi.json'}",
)

setup_exception_handlers(app)

register_middlewares(app)

register_router(app)
