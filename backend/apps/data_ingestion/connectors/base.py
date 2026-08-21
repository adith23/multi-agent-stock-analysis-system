from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from apps.core.utils.circuit_breaker import CircuitBreaker
from apps.core.utils.retry import RetryPolicy, retry_transient
from apps.data_ingestion.domain import (
    ConnectorTransientError,
    SourceType,
)


class BaseConnector(ABC):
    """Template method for resilient, opinion-free vendor access."""

    source_type: SourceType
    supported_categories: frozenset[str] = frozenset()

    def __init__(
        self,
        config: Mapping[str, Any] | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.config = dict(config or {})
        self._client = client
        policy = RetryPolicy(
            attempts=int(self.config.get("retry_attempts", 3)),
            initial_wait_seconds=float(self.config.get("retry_initial_seconds", 0.25)),
            maximum_wait_seconds=float(self.config.get("retry_max_seconds", 4.0)),
            retryable_exceptions=(
                ConnectorTransientError,
                TimeoutError,
                ConnectionError,
            ),
        )
        self._retrying_fetch = retry_transient(policy)(self._fetch_once)
        self._breaker = CircuitBreaker(
            failure_threshold=int(self.config.get("failure_threshold", 5)),
            recovery_timeout=float(self.config.get("recovery_timeout_seconds", 60)),
            expected_exceptions=(
                ConnectorTransientError,
                TimeoutError,
                ConnectionError,
            ),
        )

    @abstractmethod
    def fetch(self, category: str, **params: Any) -> list[dict[str, Any]]:
        """Fetch a category and return JSON-compatible raw records."""

    def fetch_with_resilience(self, category: str, **params: Any) -> list[dict[str, Any]]:
        if category not in self.supported_categories:
            from apps.data_ingestion.domain import UnsupportedDataTypeError

            raise UnsupportedDataTypeError(
                f"{self.source_type} does not support category {category!r}"
            )
        return self._breaker.call(self._retrying_fetch, category, **params)

    def _fetch_once(self, category: str, **params: Any) -> list[dict[str, Any]]:
        try:
            return self.fetch(category, **params)
        except (ConnectorTransientError, TimeoutError, ConnectionError):
            raise
        except Exception as exc:
            error_name = type(exc).__name__.casefold()
            message = str(exc).casefold()
            if any(
                marker in error_name or marker in message
                for marker in ("timeout", "connection", "ratelimit", "rate limit", "429")
            ):
                raise ConnectorTransientError(str(exc)) from exc
            raise

    def health_check(self) -> bool:
        try:
            self.fetch_with_resilience(next(iter(self.supported_categories)), health_check=True)
        except Exception:
            return False
        return True

    @staticmethod
    def as_records(payload: Any) -> list[dict[str, Any]]:
        if payload is None:
            return []
        if isinstance(payload, list):
            return [item if isinstance(item, dict) else {"value": item} for item in payload]
        if isinstance(payload, dict):
            return [payload]
        if hasattr(payload, "to_dict"):
            converted = payload.to_dict()
            if isinstance(converted, list):
                return converted
            if isinstance(converted, dict):
                return [converted]
        return [{"value": payload}]
