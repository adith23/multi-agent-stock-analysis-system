from __future__ import annotations

from typing import Any

from agents.base.memory import AgentMemory
from agents.base.runtime import attach_metadata, invoke_structured, require_keys
from agents.macro.prompts import ANALYSIS_TASK, PROMPT_VERSION, SYSTEM_PROMPT
from agents.macro.schemas import MacroAgentInput, MacroAgentOutput
from agents.macro.state import MacroAgentState
from agents.macro.tools import classify_regime, detect_transition, get_yield_curve

AGENT_ID = "macro"
AGENT_VERSION = "1.0.0"


def make_prepare_node(memory: AgentMemory):
    def prepare(state: MacroAgentState) -> dict[str, Any]:
        payload = MacroAgentInput.model_validate(
            {
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                **state.get("input_data", {}),
            }
        )
        data = payload.model_dump(mode="json")
        regime = data.get("regime_output")
        transition: dict[str, Any] = {"transition_detected": False}
        if regime is None:
            require_keys(data, "regime_features", "regime_model_path")
            regime = classify_regime.invoke(
                {"features": data["regime_features"], "model_path": data["regime_model_path"]}
            )
            transition = detect_transition.invoke(
                {"features": data["regime_features"], "model_path": data["regime_model_path"]}
            )
        curve = (
            get_yield_curve.invoke({"yields": data["yield_curve"]}) if data["yield_curve"] else {}
        )
        return {
            "macro_data": data["macro_indicators"],
            "regime": regime,
            "transition": transition,
            "yield_curve": curve,
            "prior_context": memory.recent(state["ticker"]),
            "tool_outputs": {"regime": regime, "transition": transition, "yield_curve": curve},
            "trace": [*state.get("trace", []), "macro.prepare"],
        }

    return prepare


def make_analyze_node(llm: Any):
    def analyze(state: MacroAgentState) -> dict[str, Any]:
        output = invoke_structured(
            llm,
            MacroAgentOutput,
            system_prompt=SYSTEM_PROMPT,
            task=ANALYSIS_TASK,
            context={
                "ticker": state["ticker"],
                "indicators": state.get("macro_data", []),
                "regime_model": state.get("regime", {}),
                "transition": state.get("transition", {}),
                "yield_curve": state.get("yield_curve", {}),
                "prior_regimes": state.get("prior_context", []),
            },
        )
        return {
            "agent_output": attach_metadata(
                output,
                agent_id=AGENT_ID,
                agent_version=AGENT_VERSION,
                prompt_version=PROMPT_VERSION,
            ),
            "trace": [*state.get("trace", []), "macro.analyze"],
        }

    return analyze
