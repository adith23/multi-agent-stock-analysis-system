from __future__ import annotations

from typing import Any


class PMMemory:
    """Read-only prior decision context until Phase 5 adds portfolio recommendations."""

    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        from apps.research.repositories import ResearchRepository

        return ResearchRepository().recent_decision_memos(ticker, limit=limit)
