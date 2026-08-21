from __future__ import annotations

from typing import Any

from agents.base.memory import AgentMemory
from agents.base.runtime import attach_metadata, invoke_structured
from agents.risk.prompts import ANALYSIS_TASK, PROMPT_VERSION, SYSTEM_PROMPT
from agents.risk.schemas import RiskAgentInput, RiskAgentOutput
from agents.risk.state import RiskAgentState
from agents.risk.tools import assess_liquidity, check_concentration, compute_var, run_stress_test
from rules.risk_limits.limit_checker import RiskLimitChecker

AGENT_ID = "risk"
AGENT_VERSION = "1.0.0"


def make_prepare_node(memory: AgentMemory):
    def prepare(state: RiskAgentState) -> dict[str, Any]:
        payload = RiskAgentInput.model_validate(
            {
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                **state.get("input_data", {}),
            }
        )
        var = compute_var.invoke({"var_inputs": payload.var_inputs}) if payload.var_inputs else {}
        stress = (
            run_stress_test.invoke({"stress_inputs": payload.stress_inputs})
            if payload.stress_inputs
            else {}
        )
        concentration = (
            check_concentration.invoke({"concentration_inputs": payload.concentration_inputs})
            if payload.concentration_inputs
            else {}
        )
        liquidity = (
            assess_liquidity.invoke({"liquidity_inputs": payload.liquidity_inputs})
            if payload.liquidity_inputs
            else {}
        )
        limit_result = RiskLimitChecker(payload.limits).evaluate(payload.limit_metrics)
        return {
            "risk_metrics": {
                "proposed_trade": payload.proposed_trade,
                "portfolio_state": payload.portfolio_state,
            },
            "var_result": var,
            "stress_result": stress,
            "concentration_result": concentration,
            "liquidity_result": liquidity,
            "limit_result": limit_result,
            "prior_context": memory.recent(state["ticker"]),
            "tool_outputs": {
                "var": var,
                "stress": stress,
                "concentration": concentration,
                "liquidity": liquidity,
                "limits": limit_result,
            },
            "trace": [*state.get("trace", []), "risk.prepare"],
        }

    return prepare


def make_analyze_node(llm: Any):
    def analyze(state: RiskAgentState) -> dict[str, Any]:
        output = invoke_structured(
            llm,
            RiskAgentOutput,
            system_prompt=SYSTEM_PROMPT,
            task=ANALYSIS_TASK,
            context={
                "ticker": state["ticker"],
                "trade_and_portfolio": state.get("risk_metrics", {}),
                "var": state.get("var_result", {}),
                "stress": state.get("stress_result", {}),
                "concentration": state.get("concentration_result", {}),
                "liquidity": state.get("liquidity_result", {}),
                "binding_limit_decision": state.get("limit_result", {}),
                "prior_risk_decisions": state.get("prior_context", []),
            },
        )
        binding = str(state.get("limit_result", {}).get("decision", "pass"))
        if binding in {"block", "escalate", "reduce_size"}:
            output.disposition = binding
            output.approved = False
        return {
            "agent_output": attach_metadata(
                output,
                agent_id=AGENT_ID,
                agent_version=AGENT_VERSION,
                prompt_version=PROMPT_VERSION,
            ),
            "trace": [*state.get("trace", []), "risk.analyze"],
        }

    return analyze
