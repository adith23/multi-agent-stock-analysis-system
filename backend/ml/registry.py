from __future__ import annotations

import threading
from collections.abc import Callable

from .base import MLModel


class MLModelRegistry:
    """Thread-safe lazy factory with explicit model version metadata."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], MLModel]] = {}
        self._instances: dict[str, MLModel] = {}
        self._lock = threading.RLock()

    def register(self, name: str, factory: Callable[[], MLModel]) -> None:
        with self._lock:
            if name in self._factories and self._factories[name] is not factory:
                raise ValueError(f"model {name!r} is already registered")
            self._factories[name] = factory

    def get(self, name: str) -> MLModel:
        with self._lock:
            if name not in self._factories:
                raise KeyError(f"unknown ML model: {name}")
            if name not in self._instances:
                self._instances[name] = self._factories[name]()
            return self._instances[name]

    def available(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._factories))

    def clear(self) -> None:
        with self._lock:
            self._instances.clear()


ml_model_registry = MLModelRegistry()
