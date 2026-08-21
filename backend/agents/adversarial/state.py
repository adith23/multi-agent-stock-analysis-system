from __future__ import annotations

from typing import Any, NotRequired

from agents.base.state import AgentState


class AdversarialState(AgentState):
    specialist_outputs: dict[str, dict[str, Any]]
    debate_round: int
    bull_arguments: list[dict[str, Any]]
    bear_arguments: list[dict[str, Any]]
    moderator_decision: NotRequired[dict[str, Any]]
    premortem: NotRequired[dict[str, Any]]
    prior_context: NotRequired[list[dict[str, Any]]]
