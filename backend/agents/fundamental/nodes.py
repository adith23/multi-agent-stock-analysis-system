from __future__ import annotations

from typing import Any

from agents.base.memory import AgentMemory
from agents.base.runtime import attach_metadata, invoke_structured
from agents.fundamental.prompts import ANALYSIS_TASK, PROMPT_VERSION, SYSTEM_PROMPT
from agents.fundamental.schemas import FundamentalAgentInput, FundamentalAgentOutput
from agents.fundamental.state import FundamentalAgentState
from agents.fundamental.tools import check_earnings_quality, compare_peers, run_valuation

AGENT_ID = "fundamental"
AGENT_VERSION = "1.0.0"


def make_prepare_node(memory: AgentMemory):
    def prepare(state: FundamentalAgentState) -> dict[str, Any]:
        payload = FundamentalAgentInput.model_validate(
            {
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                **state.get("input_data", {}),
            }
        )
        data = payload.model_dump(mode="json")
        valuation = (
            run_valuation.invoke(
                {
                    "dcf_inputs": data["dcf_inputs"],
                    "multiples_inputs": data["multiples_inputs"],
                }
            )
            if data["dcf_inputs"] or data["multiples_inputs"]
            else {}
        )
        quality = (
            check_earnings_quality.invoke({"financials": data["earnings_quality_inputs"]})
            if data["earnings_quality_inputs"]
            else {}
        )
        peers = (
            compare_peers.invoke({"peer_inputs": data["peer_inputs"]})
            if data["peer_inputs"]
            else {}
        )
        return {
            "financials": data["financials"],
            "company_profile": data["company_profile"],
            "valuation": valuation,
            "earnings_quality": quality,
            "peer_comparison": peers,
            "prior_context": memory.recent(state["ticker"]),
            "tool_outputs": {"valuation": valuation, "earnings_quality": quality, "peers": peers},
            "trace": [*state.get("trace", []), "fundamental.prepare"],
        }

    return prepare


def make_analyze_node(llm: Any):
    def analyze(state: FundamentalAgentState) -> dict[str, Any]:
        output = invoke_structured(
            llm,
            FundamentalAgentOutput,
            system_prompt=SYSTEM_PROMPT,
            task=ANALYSIS_TASK,
            context={
                "ticker": state["ticker"],
                "financials": state.get("financials", {}),
                "company_profile": state.get("company_profile", {}),
                "valuation": state.get("valuation", {}),
                "earnings_quality": state.get("earnings_quality", {}),
                "peer_comparison": state.get("peer_comparison", {}),
                "prior_theses": state.get("prior_context", []),
                "macro_context": state.get("input_data", {}).get("macro_context", {}),
            },
        )
        return {
            "agent_output": attach_metadata(
                output,
                agent_id=AGENT_ID,
                agent_version=AGENT_VERSION,
                prompt_version=PROMPT_VERSION,
            ),
            "trace": [*state.get("trace", []), "fundamental.analyze"],
        }

    return analyze
