from __future__ import annotations

from abc import ABC
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

import numpy as np

from apps.core.domain.interfaces import IDeterministicEngine

from .exceptions import EngineInputError, InsufficientDataError


class DeterministicEngine(IDeterministicEngine, ABC):
    """Common validation helpers for pure, versioned calculation engines."""

    VERSION: ClassVar[str] = "1.0.0"

    @property
    def engine_version(self) -> str:
        return self.VERSION

    @staticmethod
    def require(inputs: Mapping[str, Any], *keys: str) -> None:
        missing = [key for key in keys if key not in inputs or inputs[key] is None]
        if missing:
            raise EngineInputError(f"missing required inputs: {', '.join(missing)}")

    @staticmethod
    def vector(
        value: Sequence[float] | np.ndarray,
        *,
        name: str,
        minimum_length: int = 1,
        finite: bool = True,
    ) -> np.ndarray:
        result = np.asarray(value, dtype=float)
        if result.ndim != 1:
            raise EngineInputError(f"{name} must be one-dimensional")
        if len(result) < minimum_length:
            raise InsufficientDataError(f"{name} requires at least {minimum_length} observations")
        if finite and not np.isfinite(result).all():
            raise EngineInputError(f"{name} contains non-finite values")
        return result

    @staticmethod
    def matrix(value: Any, *, name: str, square: bool = False) -> np.ndarray:
        result = np.asarray(value, dtype=float)
        if result.ndim != 2:
            raise EngineInputError(f"{name} must be two-dimensional")
        if square and result.shape[0] != result.shape[1]:
            raise EngineInputError(f"{name} must be square")
        if not np.isfinite(result).all():
            raise EngineInputError(f"{name} contains non-finite values")
        return result

    @staticmethod
    def safe_divide(numerator: float, denominator: float, *, default: float = 0.0) -> float:
        return float(numerator / denominator) if denominator else default

    @staticmethod
    def normalized_weights(weights: Any) -> np.ndarray:
        result = np.asarray(weights, dtype=float)
        if result.ndim != 1 or not len(result):
            raise EngineInputError("weights must be a non-empty vector")
        if not np.isfinite(result).all() or (result < 0).any():
            raise EngineInputError("weights must be finite and non-negative")
        total = result.sum()
        if total <= 0:
            raise EngineInputError("weights must have a positive sum")
        return result / total
