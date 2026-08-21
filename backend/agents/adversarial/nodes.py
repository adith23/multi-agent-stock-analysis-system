from __future__ import annotations

from typing import Any

from agents.adversarial.prompts import (
    BEAR_SYSTEM_PROMPT,
    BULL_SYSTEM_PROMPT,
    FINALIZE_SYSTEM_PROMPT,
    MODERATOR_SYSTEM_PROMPT,
    PROMPT_VERSION,
)
from agents.adversarial.schemas import (
    AdversarialAgentInput,
    BullBearDecisionMemo,
    DebateArgument,
    ModeratorDecision,
)
from agents.adversarial.state import AdversarialState
from agents.adversarial.tools import run_premortem
from agents.base.memory import AgentMemory
from agents.base.runtime import attach_metadata, invoke_structured

AGENT_ID = "adversarial"
AGENT_VERSION = "1.0.0"


def make_prepare_node(memory: AgentMemory):
    def prepare(state: AdversarialState) -> dict[str, Any]:
        payload = AdversarialAgentInput.model_validate(
            {
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                "specialist_outputs": state["specialist_outputs"],
                **state.get("input_data", {}),
            }
        )
        premortem = (
            run_premortem.invoke({"scenario_inputs": payload.scenario_inputs})
            if payload.scenario_inputs
            else {}
        )
        return {
            "specialist_outputs": payload.specialist_outputs,
            "debate_round": 0,
            "bull_arguments": [],
            "bear_arguments": [],
            "premortem": premortem,
            "prior_context": memory.recent(state["ticker"]),
            "tool_outputs": {"premortem": premortem},
            "metadata": {"max_debate_rounds": payload.max_debate_rounds},
            "trace": [*state.get("trace", []), "adversarial.prepare"],
        }

    return prepare


def make_bull_node(llm: Any):
    def bull(state: AdversarialState) -> dict[str, Any]:
        argument = invoke_structured(
            llm,
            DebateArgument,
            system_prompt=BULL_SYSTEM_PROMPT,
            task="Present or strengthen the evidence-supported bull case.",
            context={
                "specialists": state["specialist_outputs"],
                "prior_bear_arguments": state["bear_arguments"],
                "premortem": state.get("premortem", {}),
            },
        )
        return {
            "bull_arguments": [*state["bull_arguments"], argument.model_dump(mode="json")],
            "debate_round": state["debate_round"] + 1,
            "trace": [*state.get("trace", []), "adversarial.bull"],
        }

    return bull


def make_bear_node(llm: Any):
    def bear(state: AdversarialState) -> dict[str, Any]:
        argument = invoke_structured(
            llm,
            DebateArgument,
            system_prompt=BEAR_SYSTEM_PROMPT,
            task="Attack the current thesis and identify failure conditions.",
            context={
                "specialists": state["specialist_outputs"],
                "bull_arguments": state["bull_arguments"],
                "prior_bear_arguments": state["bear_arguments"],
                "premortem": state.get("premortem", {}),
            },
        )
        return {
            "bear_arguments": [*state["bear_arguments"], argument.model_dump(mode="json")],
            "trace": [*state.get("trace", []), "adversarial.bear"],
        }

    return bear


def make_moderator_node(llm: Any):
    def moderator(state: AdversarialState) -> dict[str, Any]:
        maximum = int(state.get("metadata", {}).get("max_debate_rounds", 3))
        if state["debate_round"] >= maximum:
            decision = ModeratorDecision(
                verdict="conclude",
                rationale="Configured maximum debate rounds reached.",
            )
        else:
            decision = invoke_structured(
                llm,
                ModeratorDecision,
                system_prompt=MODERATOR_SYSTEM_PROMPT,
                task="Decide whether another debate round adds material information.",
                context={
                    "bull_arguments": state["bull_arguments"],
                    "bear_arguments": state["bear_arguments"],
                    "round": state["debate_round"],
                    "maximum_rounds": maximum,
                },
            )
        return {
            "moderator_decision": decision.model_dump(mode="json"),
            "trace": [*state.get("trace", []), "adversarial.moderator"],
        }

    return moderator


def route_after_moderator(state: AdversarialState) -> str:
    return "finalize" if state["moderator_decision"]["verdict"] == "conclude" else "bull"


def make_finalize_node(llm: Any):
    def finalize(state: AdversarialState) -> dict[str, Any]:
        output = invoke_structured(
            llm,
            BullBearDecisionMemo,
            system_prompt=FINALIZE_SYSTEM_PROMPT,
            task="Produce the final balanced decision memo.",
            context={
                "specialists": state["specialist_outputs"],
                "bull_arguments": state["bull_arguments"],
                "bear_arguments": state["bear_arguments"],
                "premortem": state.get("premortem", {}),
                "prior_decisions": state.get("prior_context", []),
            },
        )
        return {
            "agent_output": attach_metadata(
                output,
                agent_id=AGENT_ID,
                agent_version=AGENT_VERSION,
                prompt_version=PROMPT_VERSION,
            ),
            "trace": [*state.get("trace", []), "adversarial.finalize"],
        }

    return finalize
