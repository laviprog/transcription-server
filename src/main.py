from fastapi import FastAPI
from scalar_fastapi import Theme, add_scalar_reference
from starlette.middleware.cors import CORSMiddleware

from src.middlewares import LogMiddleware

from .config import settings
from .exceptions.handlers import setup_exception_handlers
from .exceptions.responses import error_responses
from .lifecycle import lifespan
from .log_config import configure as configure_logging
from .routes import routes_register

configure_logging()

app = FastAPI(
    title="Speech Recognition API",
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

app.add_middleware(LogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

routes_register(app)
