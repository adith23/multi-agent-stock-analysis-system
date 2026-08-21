from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def get_specialist_reports(analysis_run_id: str) -> list[dict[str, Any]]:
    """Fetch all versioned specialist outputs for an analysis run."""

    from apps.research.repositories import ResearchRepository

    return ResearchRepository().specialist_reports_for_run(analysis_run_id)
