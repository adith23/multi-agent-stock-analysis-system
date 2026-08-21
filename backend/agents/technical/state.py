from __future__ import annotations

from typing import Any, NotRequired

from agents.base.state import AgentState


class TechnicalAgentState(AgentState):
    ohlcv: NotRequired[list[dict[str, Any]]]
    indicators: NotRequired[dict[str, Any]]
    patterns: NotRequired[dict[str, Any]]
    trend: NotRequired[dict[str, Any]]
    relative_strength: NotRequired[dict[str, Any]]
    prior_context: NotRequired[list[dict[str, Any]]]
