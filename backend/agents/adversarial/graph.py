from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.adversarial.nodes import (
    make_bear_node,
    make_bull_node,
    make_finalize_node,
    make_moderator_node,
    make_prepare_node,
    route_after_moderator,
)
from agents.adversarial.state import AdversarialState
from agents.base.memory import AgentMemory, NullMemory
from llm.providers.registry import get_llm


def build_adversarial_agent_graph(
    *,
    llm: Any | None = None,
    memory: AgentMemory | None = None,
    checkpointer: Any = None,
):
    model = llm or get_llm(temperature=0.4)
    builder = StateGraph(AdversarialState)
    builder.add_node("prepare", make_prepare_node(memory or NullMemory()))
    builder.add_node("bull", make_bull_node(model))
    builder.add_node("bear", make_bear_node(model))
    builder.add_node("moderator", make_moderator_node(model))
    builder.add_node("finalize", make_finalize_node(model))
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "bull")
    builder.add_edge("bull", "bear")
    builder.add_edge("bear", "moderator")
    builder.add_conditional_edges(
        "moderator",
        route_after_moderator,
        {"bull": "bull", "finalize": "finalize"},
    )
    builder.add_edge("finalize", END)
    return builder.compile(checkpointer=checkpointer)
