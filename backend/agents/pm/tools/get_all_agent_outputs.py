from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def get_all_agent_outputs(analysis_run_id: str) -> dict[str, Any]:
    """Fetch the latest report for every specialist in an analysis run."""

    from apps.research.repositories import ResearchRepository

    reports = ResearchRepository().specialist_reports_for_run(analysis_run_id)
    output: dict[str, Any] = {}
    for report in reports:
        output.setdefault(
            report["specialist_type"],
            {
                key: report[key]
                for key in (
                    "thesis",
                    "summary",
                    "evidence",
                    "assumptions",
                    "limitations",
                    "confidence",
                    "version",
                )
            },
        )
    return output
