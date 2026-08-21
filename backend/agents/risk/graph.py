from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.base.memory import AgentMemory, NullMemory
from agents.risk.nodes import make_analyze_node, make_prepare_node
from agents.risk.state import RiskAgentState
from llm.providers.registry import get_llm


def build_risk_agent_graph(
    *,
    llm: Any | None = None,
    memory: AgentMemory | None = None,
    checkpointer: Any = None,
):
    builder = StateGraph(RiskAgentState)
    builder.add_node("prepare", make_prepare_node(memory or NullMemory()))
    builder.add_node("analyze", make_analyze_node(llm or get_llm(temperature=0.1)))
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "analyze")
    builder.add_edge("analyze", END)
    return builder.compile(checkpointer=checkpointer)
