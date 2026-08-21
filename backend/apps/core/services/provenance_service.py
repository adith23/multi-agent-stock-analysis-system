"""Decorator-based provenance capture for deterministic transformations."""

from __future__ import annotations

import functools
import inspect
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, ParamSpec

from apps.core.utils.hashing import content_hash

P = ParamSpec("P")


@dataclass(frozen=True, slots=True)
class ProvenanceMetadata:
    source_type: str
    operation: str
    captured_at: datetime
    input_hash: str
    output_hash: str
    source_id: str = ""
    version: str = "1"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProvenanceResult[R]:
    value: R
    provenance: ProvenanceMetadata


def _capture[R](
    *,
    function_name: str,
    source_type: str,
    source_id: str,
    version: str,
    arguments: dict[str, Any],
    result: R,
) -> ProvenanceResult[R]:
    metadata = ProvenanceMetadata(
        source_type=source_type,
        source_id=source_id,
        operation=function_name,
        version=version,
        captured_at=datetime.now(UTC),
        input_hash=content_hash(arguments),
        output_hash=content_hash(result),
    )
    return ProvenanceResult(value=result, provenance=metadata)


def with_provenance(
    *,
    source_type: str,
    source_id: str = "",
    version: str = "1",
) -> Any:
    """Wrap a transform result with immutable, content-addressed provenance."""

    if not source_type.strip():
        raise ValueError("source_type is required")

    def decorate(function: Any) -> Any:
        signature = inspect.signature(function)

        if inspect.iscoroutinefunction(function):

            @functools.wraps(function)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                bound = signature.bind_partial(*args, **kwargs)
                result = await function(*args, **kwargs)
                return _capture(
                    function_name=function.__qualname__,
                    source_type=source_type,
                    source_id=source_id,
                    version=version,
                    arguments=dict(bound.arguments),
                    result=result,
                )

            return async_wrapper

        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            bound = signature.bind_partial(*args, **kwargs)
            result = function(*args, **kwargs)
            return _capture(
                function_name=function.__qualname__,
                source_type=source_type,
                source_id=source_id,
                version=version,
                arguments=dict(bound.arguments),
                result=result,
            )

        return wrapper

    return decorate
