from __future__ import annotations

from typing import Any


class FundamentalMemory:
    """Prior versioned fundamental theses for continuity and change detection."""

    def recent(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        from apps.research.repositories import ResearchRepository

        return ResearchRepository().recent_specialist_reports(
            ticker,
            "fundamental",
            limit=limit,
        )
