"""Thread-safe circuit breaker for unreliable external dependencies."""

from __future__ import annotations

import functools
import inspect
import threading
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any, ParamSpec, TypeVar

from apps.core.domain.exceptions import CircuitBreakerOpenError

P = ParamSpec("P")
R = TypeVar("R")


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Fail fast after repeated failures and probe again after a cool-down."""

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: tuple[type[BaseException], ...] = (Exception,),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if recovery_timeout < 0:
            raise ValueError("recovery_timeout cannot be negative")
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self._clock = clock
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None
        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._transition_to_half_open_if_due()
            return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failure_count

    def _transition_to_half_open_if_due(self) -> None:
        if (
            self._state is CircuitState.OPEN
            and self._opened_at is not None
            and self._clock() - self._opened_at >= self.recovery_timeout
        ):
            self._state = CircuitState.HALF_OPEN

    def _before_call(self) -> None:
        with self._lock:
            self._transition_to_half_open_if_due()
            if self._state is CircuitState.OPEN:
                raise CircuitBreakerOpenError("dependency circuit is open")

    def _record_success(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._opened_at = None

    def _record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            if (
                self._state is CircuitState.HALF_OPEN
                or self._failure_count >= self.failure_threshold
            ):
                self._state = CircuitState.OPEN
                self._opened_at = self._clock()

    def call(self, function: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        self._before_call()
        try:
            result = function(*args, **kwargs)
        except self.expected_exceptions:
            self._record_failure()
            raise
        self._record_success()
        return result

    async def call_async(
        self,
        function: Callable[P, Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        self._before_call()
        try:
            result = await function(*args, **kwargs)
        except self.expected_exceptions:
            self._record_failure()
            raise
        self._record_success()
        return result

    def reset(self) -> None:
        self._record_success()


def circuit_breaker(
    breaker: CircuitBreaker | None = None,
    **options: Any,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorate a synchronous or asynchronous dependency call."""

    instance = breaker or CircuitBreaker(**options)

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(function):

            @functools.wraps(function)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                return await instance.call_async(function, *args, **kwargs)  # type: ignore[arg-type]

            async_wrapper.circuit_breaker = instance  # type: ignore[attr-defined]
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return instance.call(function, *args, **kwargs)

        wrapper.circuit_breaker = instance  # type: ignore[attr-defined]
        return wrapper

    return decorate
