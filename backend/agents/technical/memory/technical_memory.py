from __future__ import annotations

from typing import Any


class TechnicalMemory:
    """Prior technical-signal snapshots for change detection."""

    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        from apps.signals.repositories import SignalRepository

        return SignalRepository().recent_technical_signals(ticker, limit=limit)
