import time
import uuid

import structlog
from fastapi.middleware.cors import CORSMiddleware

from transcription_server.core.config import settings

log = structlog.get_logger(__name__)


def register_middlewares(app):
    @app.middleware("http")
    async def log_middleware(request, call_next):
        correlation_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
            request.client.host if request.client else None
        )

        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            ip_address=ip,
        )

        start = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        except Exception:
            log.exception(
                "Unhandled Exception",
                request_method=request.method,
                request_url=str(request.url),
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status = getattr(response, "status_code", None)
            log.info("Request completed", status_code=status, duration_ms=duration_ms)

            if response is not None:
                response.headers.setdefault("X-Request-Id", correlation_id)

            # unbind context variables
            structlog.contextvars.unbind_contextvars(
                "correlation_id", "method", "path", "ip_address"
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS_LIST,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
