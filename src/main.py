from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import src.database.models  # noqa
from src.middlewares import LogMiddleware

from .config import settings
from .exceptions.handlers import setup_exception_handlers
from .exceptions.responses import error_responses
from .lifecycle import lifespan
from .logging import configure as configure_logging
from .routes import routes_register

configure_logging()

app = FastAPI(
    title="Speech Recognition API",
    version="0.0.1",
    docs_url="/docs/swagger",
    openapi_url="/openapi.json",
    root_path=settings.ROOT_PATH,
    responses=error_responses,
    lifespan=lifespan,
)

setup_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LogMiddleware)

routes_register(app)
