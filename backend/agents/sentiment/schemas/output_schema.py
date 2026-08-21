from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agents.base.contracts import AgentOutputBase, AgentStance


class RankedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str
    relevance: float = Field(ge=0.0, le=1.0)
    importance: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)


class SentimentAgentOutput(AgentOutputBase):
    stance: AgentStance
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    narrative_direction: str
    attention_level: str
    crowding_risk: bool
    ranked_events: list[RankedEvent] = Field(default_factory=list)
    event_tags: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
