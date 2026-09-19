import structlog
from celery.signals import (
    setup_logging,
    worker_process_init,
    worker_process_shutdown,
)

from transcription_server.core.log_config import configure as configure_logging
from transcription_server.worker.db import dispose_db_sync, init_db_sync

log = structlog.get_logger()


@setup_logging.connect
def _setup_logging(**_):
    configure_logging(service="worker")


@worker_process_init.connect
def _proc_init(**_):
    from transcription_server.domain.transcription.enums import Model
    from transcription_server.worker.state import get_transcriber

    configure_logging(service="worker")

    log.info("Initializing resources...")
    init_db_sync()
    get_transcriber(preload=[Model.TURBO])
    log.info("Initialization complete")


@worker_process_shutdown.connect
def _proc_shutdown(**_):
    from transcription_server.worker.state import cleanup_transcriber

    log.info("Cleaning up resources...")
    dispose_db_sync()
    cleanup_transcriber()
    log.info("Shutdown complete")
