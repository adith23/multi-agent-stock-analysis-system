from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def get_portfolio_state(portfolio_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Validate a repository-supplied portfolio snapshot for isolated agent execution."""

    if not portfolio_id.strip() or not snapshot:
        raise ValueError("portfolio_id and a non-empty portfolio snapshot are required")
    return {"portfolio_id": portfolio_id, **snapshot}
