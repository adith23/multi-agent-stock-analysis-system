from __future__ import annotations

from typing import Any

from agents.base.memory import AgentMemory
from agents.base.runtime import attach_metadata, invoke_structured
from agents.pm.prompts import PROMPT_VERSION, SYNTHESIS_TASK, SYSTEM_PROMPT
from agents.pm.schemas import HumanReview, PMAgentInput, PMRecommendation
from agents.pm.state import PMAgentState
from agents.pm.tools import (
    compute_position_size,
    generate_exit_strategy,
    identify_catalysts,
    rank_ideas,
    run_portfolio_optimization,
)
from apps.core.domain.enums import ActionSignal

AGENT_ID = "pm"
AGENT_VERSION = "1.0.0"


def make_prepare_node(memory: AgentMemory):
    def prepare(state: PMAgentState) -> dict[str, Any]:
        payload = PMAgentInput.model_validate(
            {
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                **state.get("input_data", {}),
            }
        )
        support: dict[str, Any] = {
            "conviction": payload.conviction,
            "compliance": payload.compliance,
            "mandate": payload.mandate,
        }
        if payload.sizing_inputs:
            values = dict(payload.sizing_inputs)
            methodology = str(values.pop("methodology"))
            support["position_size"] = compute_position_size.invoke(
                {"methodology": methodology, "inputs": values}
            )
        if payload.exit_inputs:
            support["exit_strategy"] = generate_exit_strategy.invoke(
                {"inputs": payload.exit_inputs}
            )
        if payload.optimization_inputs:
            values = payload.optimization_inputs
            support["portfolio_optimization"] = run_portfolio_optimization.invoke(values)
        if payload.candidate_ideas:
            criteria = list(payload.context.get("ranking_criteria", []))
            support["ranked_ideas"] = (
                rank_ideas.invoke(
                    {
                        "ideas": payload.candidate_ideas,
                        "criteria": criteria,
                        "weights": payload.context.get("ranking_weights", [1.0] * len(criteria)),
                        "beneficial": payload.context.get(
                            "ranking_beneficial", [True] * len(criteria)
                        ),
                    }
                )
                if criteria
                else payload.candidate_ideas
            )
        support["catalysts"] = identify_catalysts.invoke({"events": payload.catalyst_events})
        return {
            "all_agent_outputs": payload.agent_outputs,
            "decision_support": support,
            "prior_context": memory.recent(state["ticker"]),
            "tool_outputs": support,
            "trace": [*state.get("trace", []), "pm.prepare"],
        }

    return prepare


def make_synthesize_node(llm: Any):
    def synthesize(state: PMAgentState) -> dict[str, Any]:
        output = invoke_structured(
            llm,
            PMRecommendation,
            system_prompt=SYSTEM_PROMPT,
            task=SYNTHESIS_TASK,
            context={
                "ticker": state["ticker"],
                "agent_outputs": state.get("all_agent_outputs", {}),
                "decision_support": state.get("decision_support", {}),
                "prior_decisions": state.get("prior_context", []),
            },
        )
        output.decision_status = "pending_review"
        risk_disposition = str(
            state.get("all_agent_outputs", {}).get("risk", {}).get("disposition", "")
        )
        compliance_decision = str(
            state.get("decision_support", {}).get("compliance", {}).get("decision", "")
        )
        if risk_disposition == "block" or compliance_decision in {"restricted", "violated"}:
            output.action = ActionSignal.NOT_BUY
            output.conditions_precedent.append(
                "Binding risk or compliance restriction must be cleared before approval."
            )
        return {
            "draft_recommendation": attach_metadata(
                output,
                agent_id=AGENT_ID,
                agent_version=AGENT_VERSION,
                prompt_version=PROMPT_VERSION,
            ),
            "trace": [*state.get("trace", []), "pm.synthesize"],
        }

    return synthesize


def human_review(state: PMAgentState) -> dict[str, Any]:
    """Validate review data injected by the approval service after the static interrupt."""

    raw = state.get("human_decision")
    if raw is None:
        raise ValueError("human_decision must be injected before resuming the PM graph")
    review = HumanReview.model_validate(raw)
    return {
        "human_decision": review.model_dump(mode="json"),
        "trace": [*state.get("trace", []), "pm.human_review"],
    }


def finalize(state: PMAgentState) -> dict[str, Any]:
    review = state["human_decision"]
    recommendation = dict(state["draft_recommendation"])
    recommendation["decision_status"] = {
        "approve": "approved",
        "reject": "rejected",
        "defer": "deferred",
    }[review["decision"]]
    recommendation["human_review"] = review
    return {
        "agent_output": recommendation,
        "trace": [*state.get("trace", []), "pm.finalize"],
    }
