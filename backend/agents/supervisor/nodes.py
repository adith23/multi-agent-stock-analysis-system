from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agents.supervisor.state import SupervisorState

GraphFactory = Callable[..., Any]


def prepare(state: SupervisorState) -> dict[str, Any]:
    required = {"macro", "fundamental", "technical", "sentiment", "risk", "pm"}
    missing = required - state["agent_inputs"].keys()
    if missing:
        raise ValueError(f"missing supervisor agent inputs: {', '.join(sorted(missing))}")
    return {
        "current_stage": "specialists",
        "specialist_outputs": {},
        "trace": [*state.get("trace", []), "supervisor.prepare"],
    }


def make_specialist_node(
    agent_id: str,
    factory: GraphFactory,
    *,
    llm: Any,
):
    graph = factory(llm=llm, checkpointer=False)

    def run(state: SupervisorState) -> dict[str, Any]:
        result = graph.invoke(
            {
                "messages": [],
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                "input_data": state["agent_inputs"][agent_id],
                "trace": [],
            }
        )
        return {
            "parallel_results": [
                {
                    "agent_id": agent_id,
                    "output": result["agent_output"],
                    "trace": result.get("trace", []),
                }
            ]
        }

    return run


def join_specialists(state: SupervisorState) -> dict[str, Any]:
    outputs = {item["agent_id"]: item["output"] for item in state["parallel_results"]}
    return {
        "specialist_outputs": outputs,
        "current_stage": "adversarial",
        "trace": [*state.get("trace", []), "supervisor.join_specialists"],
    }


def make_adversarial_node(factory: GraphFactory, *, llm: Any):
    graph = factory(llm=llm, checkpointer=False)

    def run(state: SupervisorState) -> dict[str, Any]:
        inputs = dict(state["agent_inputs"].get("adversarial", {}))
        result = graph.invoke(
            {
                "messages": [],
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                "specialist_outputs": state["specialist_outputs"],
                "input_data": inputs,
                "debate_round": 0,
                "bull_arguments": [],
                "bear_arguments": [],
                "trace": [],
            }
        )
        return {
            "adversarial_output": result["agent_output"],
            "current_stage": "risk",
            "trace": [*state.get("trace", []), "supervisor.adversarial"],
        }

    return run


def make_risk_node(factory: GraphFactory, *, llm: Any):
    graph = factory(llm=llm, checkpointer=False)

    def run(state: SupervisorState) -> dict[str, Any]:
        inputs = {
            **state["agent_inputs"]["risk"],
            "context": {
                **state["agent_inputs"]["risk"].get("context", {}),
                "specialist_outputs": state["specialist_outputs"],
                "adversarial_output": state["adversarial_output"],
            },
        }
        result = graph.invoke(
            {
                "messages": [],
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                "input_data": inputs,
                "trace": [],
            }
        )
        return {
            "risk_output": result["agent_output"],
            "current_stage": "pm_review",
            "trace": [*state.get("trace", []), "supervisor.risk"],
        }

    return run


def make_pm_node(factory: GraphFactory, *, llm: Any):
    graph = factory(llm=llm, checkpointer=False, interrupt_before_review=False)

    def run(state: SupervisorState) -> dict[str, Any]:
        outputs = {
            **state["specialist_outputs"],
            "adversarial": state["adversarial_output"],
            "risk": state["risk_output"],
        }
        inputs = {**state["agent_inputs"]["pm"], "agent_outputs": outputs}
        result = graph.invoke(
            {
                "messages": [],
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                "input_data": inputs,
                "human_decision": state.get("human_decision"),
                "trace": [],
            }
        )
        return {
            "pm_output": result["agent_output"],
            "agent_output": result["agent_output"],
            "current_stage": "completed",
            "trace": [*state.get("trace", []), "supervisor.pm"],
        }

    return run


def mark_risk_blocked(state: SupervisorState) -> dict[str, Any]:
    """Preserve block status while still routing PM to issue a Not-Buy decision."""

    return {
        "current_stage": "blocked_pm_review",
        "trace": [*state.get("trace", []), "supervisor.risk_blocked"],
    }
