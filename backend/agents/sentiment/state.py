from __future__ import annotations

from typing import Any, NotRequired

from agents.base.state import AgentState


class SentimentAgentState(AgentState):
    news: NotRequired[list[dict[str, Any]]]
    sentiment_results: NotRequired[list[dict[str, Any]]]
    attention: NotRequired[dict[str, Any]]
    prior_context: NotRequired[list[dict[str, Any]]]
