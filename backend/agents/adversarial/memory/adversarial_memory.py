from __future__ import annotations

from typing import Any


class AdversarialMemory:
    """Prior balanced decisions for the same security."""

    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        from apps.research.repositories import ResearchRepository

        return ResearchRepository().recent_decision_memos(ticker, limit=limit)
