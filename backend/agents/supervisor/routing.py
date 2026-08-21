from __future__ import annotations

from agents.supervisor.state import SupervisorState


def route_after_risk(state: SupervisorState) -> str:
    """Route binding blocks through a dedicated review marker."""

    disposition = str(state.get("risk_output", {}).get("disposition", "pass"))
    return "blocked" if disposition == "block" else "review"
