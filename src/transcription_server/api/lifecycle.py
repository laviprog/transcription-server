from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting application...")
    yield
    log.info("Application shut down")
