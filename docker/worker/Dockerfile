FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

ENV DOWNLOAD_ROOT=/data/models \
    TMP_DIR=/data/tmp \
    HF_HOME=/data/hf \
    TORCH_HOME=/data/torch

ENV LD_LIBRARY_PATH="/app/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib:/app/.venv/lib/python3.12/site-packages/nvidia/cublas/lib"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra worker --no-install-project

COPY src ./src

RUN mkdir -p ${DOWNLOAD_ROOT} ${TMP_DIR} && chown -R app:app /app ${DOWNLOAD_ROOT} ${TMP_DIR}
USER app

HEALTHCHECK --interval=30s --timeout=20s --start-period=600s --retries=3 \
    CMD celery -A src.workers.app:celery_app inspect ping --timeout=15 -d "celery@$(hostname)" || exit 1

CMD ["celery", "-A", "src.workers.app:celery_app", "worker", \
     "--loglevel=INFO", "--concurrency=1", "--without-gossip", "--without-mingle"]
