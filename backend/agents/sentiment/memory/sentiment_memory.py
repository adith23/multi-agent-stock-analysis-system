from __future__ import annotations

from typing import Any


class SentimentMemory:
    """Prior sentiment theses used only for narrative-change comparison."""

    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        from apps.research.repositories import ResearchRepository

        return ResearchRepository().recent_specialist_reports(
            ticker,
            "sentiment",
            limit=limit,
        )
