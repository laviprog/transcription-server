import asyncio
import os
from pathlib import Path

import structlog

log = structlog.get_logger()


def remove_file(path: str | Path | None) -> None:
    """
    Deletes a file, ignoring the case where it is already gone.
    """
    if not path:
        return
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError as e:
        log.error("Failed to remove file", path=str(path), error=str(e))


async def remove_file_async(path: str | Path | None) -> None:
    """
    Async wrapper around :func:`remove_file` that keeps the event loop free.
    """
    await asyncio.to_thread(remove_file, path)
