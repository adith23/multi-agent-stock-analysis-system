from __future__ import annotations

from typing import Any, NotRequired

from agents.base.state import AgentState


class RiskAgentState(AgentState):
    risk_metrics: NotRequired[dict[str, Any]]
    var_result: NotRequired[dict[str, Any]]
    stress_result: NotRequired[dict[str, Any]]
    concentration_result: NotRequired[dict[str, Any]]
    liquidity_result: NotRequired[dict[str, Any]]
    limit_result: NotRequired[dict[str, Any]]
    prior_context: NotRequired[list[dict[str, Any]]]
