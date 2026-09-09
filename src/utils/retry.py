import functools
import time
from collections.abc import Callable

import structlog

log = structlog.get_logger()


def retry(
    attempts: int = 2,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable:
    """
    Retries the wrapped callable on failure with exponential backoff.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            current_delay = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == attempts:
                        log.error(
                            "Attempt failed, giving up",
                            func=func.__qualname__,
                            attempt=attempt,
                            attempts=attempts,
                            error=str(e),
                        )
                        raise
                    log.warning(
                        "Attempt failed, retrying",
                        func=func.__qualname__,
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
