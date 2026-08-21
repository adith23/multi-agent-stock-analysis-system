from __future__ import annotations

from typing import Any

from pydantic import Field

from agents.base.contracts import AgentInputBase


class MacroAgentInput(AgentInputBase):
    macro_indicators: list[dict[str, Any]] = Field(default_factory=list)
    regime_output: dict[str, Any] | None = None
    regime_features: list[list[float]] | None = None
    regime_model_path: str | None = None
    yield_curve: dict[str, float] = Field(default_factory=dict)
