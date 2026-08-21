"""Repository abstractions for cross-session agent memory."""

from __future__ import annotations

from typing import Any, Protocol


class AgentMemory(Protocol):
    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        """Return prior agent decisions without exposing ORM objects."""


class NullMemory:
    """Safe default for isolated tests and stateless executions."""

    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        return []
