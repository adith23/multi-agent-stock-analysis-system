from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.base.memory import AgentMemory, NullMemory
from agents.pm.nodes import finalize, human_review, make_prepare_node, make_synthesize_node
from agents.pm.state import PMAgentState
from llm.providers.registry import get_llm


def build_pm_agent_graph(
    *,
    llm: Any | None = None,
    memory: AgentMemory | None = None,
    checkpointer: Any = None,
    interrupt_before_review: bool = True,
):
    """Build the PM graph with a mandatory checkpointed human-review breakpoint."""

    builder = StateGraph(PMAgentState)
    builder.add_node("prepare", make_prepare_node(memory or NullMemory()))
    builder.add_node("synthesize", make_synthesize_node(llm or get_llm(temperature=0.2)))
    builder.add_node("human_review", human_review)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "synthesize")
    builder.add_edge("synthesize", "human_review")
    builder.add_edge("human_review", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"] if interrupt_before_review else None,
    )
