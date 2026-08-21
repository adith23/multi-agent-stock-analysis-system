from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.base.memory import AgentMemory, NullMemory
from agents.fundamental.nodes import make_analyze_node, make_prepare_node
from agents.fundamental.state import FundamentalAgentState
from llm.providers.registry import get_llm


def build_fundamental_agent_graph(
    *,
    llm: Any | None = None,
    memory: AgentMemory | None = None,
    checkpointer: Any = None,
):
    builder = StateGraph(FundamentalAgentState)
    builder.add_node("prepare", make_prepare_node(memory or NullMemory()))
    builder.add_node("analyze", make_analyze_node(llm or get_llm(temperature=0.3)))
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "analyze")
    builder.add_edge("analyze", END)
    return builder.compile(checkpointer=checkpointer)
