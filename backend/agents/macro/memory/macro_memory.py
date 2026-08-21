from __future__ import annotations

from typing import Any


class MacroMemory:
    """Repository-backed cross-session macro regime memory."""

    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        from apps.signals.repositories import SignalRepository

        return SignalRepository().recent_regimes(limit=limit)
