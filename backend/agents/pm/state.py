from __future__ import annotations

from typing import Any, NotRequired

from agents.base.state import AgentState


class PMAgentState(AgentState):
    all_agent_outputs: NotRequired[dict[str, Any]]
    decision_support: NotRequired[dict[str, Any]]
    draft_recommendation: NotRequired[dict[str, Any]]
    human_decision: NotRequired[dict[str, Any]]
    prior_context: NotRequired[list[dict[str, Any]]]
