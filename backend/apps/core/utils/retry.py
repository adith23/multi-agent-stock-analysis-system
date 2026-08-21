"""Central retry policy for transient dependency failures."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    initial_wait_seconds: float = 0.5
    maximum_wait_seconds: float = 8.0
    jitter_seconds: float = 0.5
    retryable_exceptions: tuple[type[BaseException], ...] = (
        TimeoutError,
        ConnectionError,
    )

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts must be at least 1")
        if (
            min(
                self.initial_wait_seconds,
                self.maximum_wait_seconds,
                self.jitter_seconds,
            )
            < 0
        ):
            raise ValueError("retry delays cannot be negative")


def retry_transient(
    policy: RetryPolicy | None = None,
    **overrides: Any,
) -> Any:
    """Return a Tenacity decorator using the platform's bounded backoff policy."""

    selected = policy or RetryPolicy(**overrides)
    return retry(
        retry=retry_if_exception_type(selected.retryable_exceptions),
        stop=stop_after_attempt(selected.attempts),
        wait=wait_exponential_jitter(
            initial=selected.initial_wait_seconds,
            max=selected.maximum_wait_seconds,
            jitter=selected.jitter_seconds,
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
