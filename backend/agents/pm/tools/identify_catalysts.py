from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def identify_catalysts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize candidate catalysts with dates, probabilities, and thesis linkage."""

    return [
        {
            "name": event["name"],
            "expected_date": event.get("expected_date"),
            "probability": event.get("probability"),
            "thesis_linkage": event.get("thesis_linkage", ""),
            "source_id": event.get("source_id", ""),
        }
        for event in events
        if event.get("name")
    ]
