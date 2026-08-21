from __future__ import annotations

from contextlib import contextmanager
from typing import TypedDict
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from langgraph.graph import END, START, StateGraph

from agents.base.agent import BaseAgentGraph
from agents.base.callbacks import AgentObservabilityCallback
from agents.base.checkpointer import get_checkpointer
from agents.base.registry import AgentRegistry
from apps.core.domain.exceptions import ConfigurationError, RegistryError
from llm.config import LLMConfig
from llm.providers.base import ILLMProvider
from llm.providers.registry import LLMProviderRegistry, get_llm


class CounterState(TypedDict):
    count: int


class CounterAgent(BaseAgentGraph[CounterState]):
    agent_id = "counter"
    agent_version = "1.0.0"

    def build_graph(self):
        builder = StateGraph(CounterState)
        builder.add_node("increment", lambda state: {"count": state["count"] + 1})
        builder.add_edge(START, "increment")
        builder.add_edge("increment", END)
        return builder


class StubProvider(ILLMProvider):
    provider_id = "stub"

    def create(self, config: LLMConfig):
        return {"model": config.model}


def test_base_agent_compiles_and_invokes_langgraph() -> None:
    agent = CounterAgent()
    assert agent.invoke({"count": 1})["count"] == 2


def test_agent_registry_constructs_registered_agent() -> None:
    AgentRegistry.clear()
    AgentRegistry.register("counter", CounterAgent)

    assert isinstance(AgentRegistry.create("COUNTER"), CounterAgent)
    assert AgentRegistry.available() == ("counter",)
    with pytest.raises(RegistryError, match="already"):
        AgentRegistry.register("counter", CounterAgent)
    with pytest.raises(RegistryError, match="unknown"):
        AgentRegistry.create("missing")


def test_llm_provider_registry_is_replaceable() -> None:
    registry = LLMProviderRegistry()
    registry.register(StubProvider())
    config = LLMConfig("stub", "test-model", 0, 1, 10)

    assert registry.create(config) == {"model": "test-model"}
    assert registry.available() == ("stub",)
    with pytest.raises(RegistryError):
        registry.resolve("missing")


@override_settings(GOOGLE_API_KEY="")
def test_gemini_requires_api_key() -> None:
    with pytest.raises(ConfigurationError, match="GOOGLE_API_KEY"):
        get_llm()


@override_settings(GOOGLE_API_KEY="test-key")
def test_gemini_factory_creates_langchain_chat_model() -> None:
    model = get_llm(model="gemini-2.5-flash", temperature=0.1)
    assert model.model == "gemini-2.5-flash"


def test_checkpointer_manages_context_and_optional_setup() -> None:
    saver = MagicMock()

    @contextmanager
    def fake_context(*args, **kwargs):
        yield saver

    with (
        patch(
            "langgraph.checkpoint.postgres.PostgresSaver.from_conn_string",
            side_effect=fake_context,
        ) as factory,
        get_checkpointer("postgresql://example/test", setup=True) as checkpointer,
    ):
        assert checkpointer is saver

    factory.assert_called_once_with("postgresql://example/test")
    saver.setup.assert_called_once_with()


def test_agent_observability_callback_tracks_success_and_failure() -> None:
    callback = AgentObservabilityCallback(agent_id="test", analysis_run_id="run-1")
    callback.on_chain_start({}, {}, run_id="success")
    callback.on_chain_end({}, run_id="success")
    callback.on_chain_start({}, {}, run_id="failure")
    callback.on_chain_error(RuntimeError("boom"), run_id="failure")

    assert callback._started_at == {}
