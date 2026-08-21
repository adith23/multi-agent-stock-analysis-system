from __future__ import annotations

from typing import Any


class RiskMemory:
    """Historical risk-agent decisions without exposing private portfolio records."""

    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        from apps.research.repositories import ResearchRepository

        return ResearchRepository().recent_specialist_reports(
            ticker,
            "risk",
            limit=limit,
        )
