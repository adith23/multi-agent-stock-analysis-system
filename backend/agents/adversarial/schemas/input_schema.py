from __future__ import annotations

from typing import Any

from pydantic import Field

from agents.base.contracts import AgentInputBase


class AdversarialAgentInput(AgentInputBase):
    specialist_outputs: dict[str, dict[str, Any]] = Field(min_length=2)
    scenario_inputs: dict[str, Any] | None = None
    max_debate_rounds: int = Field(default=3, ge=1, le=5)
