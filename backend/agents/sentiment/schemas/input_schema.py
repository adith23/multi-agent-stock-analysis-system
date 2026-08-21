from __future__ import annotations

from typing import Any

from pydantic import Field

from agents.base.contracts import AgentInputBase


class SentimentAgentInput(AgentInputBase):
    news: list[dict[str, Any]] = Field(default_factory=list)
    texts: list[str] = Field(default_factory=list)
    sentiment_results: list[dict[str, Any]] | None = None
    article_counts: list[float] = Field(default_factory=list)
