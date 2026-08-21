from __future__ import annotations

from typing import Any

from agents.base.memory import AgentMemory
from agents.base.runtime import attach_metadata, invoke_structured
from agents.technical.prompts import ANALYSIS_TASK, PROMPT_VERSION, SYSTEM_PROMPT
from agents.technical.schemas import TechnicalAgentInput, TechnicalAgentOutput
from agents.technical.state import TechnicalAgentState
from agents.technical.tools import (
    classify_trend,
    compute_indicators,
    detect_patterns,
    measure_relative_strength,
)

AGENT_ID = "technical"
AGENT_VERSION = "1.0.0"


def make_prepare_node(memory: AgentMemory):
    def prepare(state: TechnicalAgentState) -> dict[str, Any]:
        payload = TechnicalAgentInput.model_validate(
            {
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                **state.get("input_data", {}),
            }
        )
        data = payload.model_dump(mode="json")
        indicators = compute_indicators.invoke({"ohlcv": data["ohlcv"]})
        latest = indicators["latest"]
        patterns = detect_patterns.invoke(
            {"ohlcv": data["ohlcv"], "atr": latest.get("atr_14") or 0.0}
        )
        trend = classify_trend.invoke(
            {"current_price": float(data["ohlcv"][-1]["close"]), "indicators": latest}
        )
        relative = (
            measure_relative_strength.invoke(
                {
                    "asset_prices": [float(bar["close"]) for bar in data["ohlcv"]],
                    "benchmark_prices": data["benchmark_prices"],
                }
            )
            if data["benchmark_prices"]
            else {}
        )
        return {
            "ohlcv": data["ohlcv"],
            "indicators": indicators,
            "patterns": patterns,
            "trend": trend,
            "relative_strength": relative,
            "prior_context": memory.recent(state["ticker"]),
            "tool_outputs": {
                "indicators": indicators["latest"],
                "patterns": patterns,
                "trend": trend,
                "relative_strength": relative,
            },
            "trace": [*state.get("trace", []), "technical.prepare"],
        }

    return prepare


def make_analyze_node(llm: Any):
    def analyze(state: TechnicalAgentState) -> dict[str, Any]:
        output = invoke_structured(
            llm,
            TechnicalAgentOutput,
            system_prompt=SYSTEM_PROMPT,
            task=ANALYSIS_TASK,
            context={
                "ticker": state["ticker"],
                "indicators": state.get("indicators", {}).get("latest", {}),
                "patterns": state.get("patterns", {}),
                "trend": state.get("trend", {}),
                "relative_strength": state.get("relative_strength", {}),
                "prior_signals": state.get("prior_context", []),
            },
        )
        return {
            "agent_output": attach_metadata(
                output,
                agent_id=AGENT_ID,
                agent_version=AGENT_VERSION,
                prompt_version=PROMPT_VERSION,
            ),
            "trace": [*state.get("trace", []), "technical.analyze"],
        }

    return analyze
