from __future__ import annotations

from typing import Any

from pydantic import Field

from agents.base.contracts import AgentInputBase


class PMAgentInput(AgentInputBase):
    agent_outputs: dict[str, Any] = Field(min_length=1)
    conviction: dict[str, Any] = Field(default_factory=dict)
    compliance: dict[str, Any] = Field(default_factory=dict)
    sizing_inputs: dict[str, Any] | None = None
    exit_inputs: dict[str, Any] | None = None
    optimization_inputs: dict[str, Any] | None = None
    candidate_ideas: list[dict[str, Any]] = Field(default_factory=list)
    catalyst_events: list[dict[str, Any]] = Field(default_factory=list)
    mandate: dict[str, Any] = Field(default_factory=dict)
