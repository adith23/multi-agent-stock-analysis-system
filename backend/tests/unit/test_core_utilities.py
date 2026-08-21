from __future__ import annotations

import asyncio

import pytest

from apps.core.domain.exceptions import CircuitBreakerOpenError
from apps.core.services import ProvenanceResult, with_provenance
from apps.core.utils.circuit_breaker import CircuitBreaker, CircuitState, circuit_breaker
from apps.core.utils.hashing import (
    content_hash,
    hamming_distance,
    redact_mapping,
    simhash,
)
from apps.core.utils.retry import RetryPolicy, retry_transient


def test_content_hash_is_canonical_and_redaction_is_recursive() -> None:
    assert content_hash({"b": 2, "a": 1}) == content_hash({"a": 1, "b": 2})
    assert len(content_hash("payload")) == 64
    assert hamming_distance(simhash("same article"), simhash("same article")) == 0
    assert redact_mapping({"password": "secret", "nested": {"api_key": "secret", "value": 1}}) == {
        "password": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]", "value": 1},
    }


def test_provenance_decorator_wraps_sync_and_async_results() -> None:
    @with_provenance(source_type="unit_test", source_id="fixture", version="2")
    def transform(value: int) -> dict[str, int]:
        return {"value": value * 2}

    @with_provenance(source_type="unit_test")
    async def async_transform(value: int) -> int:
        return value + 1

    result = transform(3)
    async_result = asyncio.run(async_transform(3))

    assert isinstance(result, ProvenanceResult)
    assert result.value == {"value": 6}
    assert result.provenance.source_id == "fixture"
    assert len(result.provenance.input_hash) == 64
    assert async_result.value == 4


def test_provenance_requires_source_type() -> None:
    with pytest.raises(ValueError, match="source_type"):
        with_provenance(source_type=" ")


def test_circuit_breaker_opens_recovers_and_resets() -> None:
    now = [0.0]
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=10,
        clock=lambda: now[0],
    )

    def fail() -> None:
        raise ConnectionError("offline")

    for _ in range(2):
        with pytest.raises(ConnectionError):
            breaker.call(fail)

    assert breaker.state is CircuitState.OPEN
    with pytest.raises(CircuitBreakerOpenError):
        breaker.call(lambda: "blocked")

    now[0] = 11
    assert breaker.state is CircuitState.HALF_OPEN
    assert breaker.call(lambda: "ok") == "ok"
    assert breaker.state is CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_breaker_decorator_supports_async_functions() -> None:
    @circuit_breaker(failure_threshold=1)
    async def operation() -> str:
        return "ok"

    assert asyncio.run(operation()) == "ok"
    assert operation.circuit_breaker.state is CircuitState.CLOSED  # type: ignore[attr-defined]


def test_retry_policy_retries_only_expected_failures() -> None:
    attempts = 0

    @retry_transient(
        RetryPolicy(
            attempts=3,
            initial_wait_seconds=0,
            maximum_wait_seconds=0,
            jitter_seconds=0,
            retryable_exceptions=(ConnectionError,),
        )
    )
    def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("temporary")
        return "recovered"

    assert flaky() == "recovered"
    assert attempts == 3


def test_invalid_resilience_configuration_is_rejected() -> None:
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=0)
    with pytest.raises(ValueError):
        RetryPolicy(attempts=0)
