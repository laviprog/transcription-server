import asyncio
import functools
import hashlib
import os
import time
import wave
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec, TypeVar

import structlog

log = structlog.get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


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


def get_filesize_bytes(path: str) -> int:
    return Path(path).stat().st_size


def wav_duration_seconds(path: str) -> float:
    with wave.open(path, "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate()
        return frames / float(rate)


def mp3_duration_seconds(path: str) -> float | None:
    from mutagen.mp3 import MP3

    # A missing or corrupt file raises MutagenError, which the caller already handles.
    info = MP3(path).info
    return float(info.length) if info is not None else None


def get_duration_seconds(path: str) -> float | None:
    suffix = Path(path).suffix.lower()
    if suffix == ".wav":
        return wav_duration_seconds(path)
    if suffix == ".mp3":
        return mp3_duration_seconds(path)
    return None


def hash_key(key_value: str) -> str:
    return hashlib.sha256(key_value.encode()).hexdigest()


def retry(
    attempts: int = 2,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Retries the wrapped callable on failure with exponential backoff.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def decorator_retry(func: Callable[P, R]) -> Callable[P, R]:
        # Not every callable is a function, so fall back to repr for the log field.
        func_name = getattr(func, "__qualname__", repr(func))

        @functools.wraps(func)
        def wrapper_retry(*args: P.args, **kwargs: P.kwargs) -> R:
            current_delay = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == attempts:
                        log.error(
                            "Attempt failed, giving up",
                            func=func_name,
                            attempt=attempt,
                            attempts=attempts,
                            error=str(e),
                        )
                        raise
                    log.warning(
                        "Attempt failed, retrying",
                        func=func_name,
                        attempt=attempt,
                        attempts=attempts,
                        delay=current_delay,
                        error=str(e),
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            raise AssertionError("unreachable")

        return wrapper_retry

    return decorator_retry
