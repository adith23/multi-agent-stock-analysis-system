from __future__ import annotations

from pydantic import Field

from agents.base.contracts import AgentOutputBase, AgentStance


class TechnicalAgentOutput(AgentOutputBase):
    stance: AgentStance
    trend_state: str
    timing_cue: str
    momentum_state: str
    support_levels: list[float] = Field(default_factory=list)
    resistance_levels: list[float] = Field(default_factory=list)
    pattern_risks: list[str] = Field(default_factory=list)
    relative_strength_view: str
    entry_conditions: list[str] = Field(default_factory=list)
    exit_conditions: list[str] = Field(default_factory=list)
