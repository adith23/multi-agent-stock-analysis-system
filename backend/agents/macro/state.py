from __future__ import annotations

from typing import Any, NotRequired

from agents.base.state import AgentState


class MacroAgentState(AgentState):
    macro_data: NotRequired[list[dict[str, Any]]]
    regime: NotRequired[dict[str, Any]]
    transition: NotRequired[dict[str, Any]]
    yield_curve: NotRequired[dict[str, Any]]
    prior_context: NotRequired[list[dict[str, Any]]]
