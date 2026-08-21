from __future__ import annotations

from typing import Any

from pydantic import Field

from agents.base.contracts import AgentInputBase


class TechnicalAgentInput(AgentInputBase):
    ohlcv: list[dict[str, Any]] = Field(min_length=35)
    benchmark_prices: list[float] = Field(default_factory=list)
    timeframe: str = "daily"
