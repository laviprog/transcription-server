import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

import structlog

log = structlog.get_logger()

P = ParamSpec("P")
R = TypeVar("R")


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
