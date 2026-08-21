"""Base class for independently testable LangGraph agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from langchain_core.runnables import RunnableConfig


class BaseAgentGraph[StateT: Mapping[str, Any]](ABC):
    """Template method around graph construction, compilation, and invocation."""

    def __init__(
        self,
        *,
        checkpointer: Any = None,
        interrupt_before: list[str] | None = None,
    ) -> None:
        self._builder = self.build_graph()
        self._graph = self._builder.compile(
            checkpointer=checkpointer,
            interrupt_before=interrupt_before,
        )

    @property
    @abstractmethod
    def agent_id(self) -> str: ...

    @property
    @abstractmethod
    def agent_version(self) -> str: ...

    @abstractmethod
    def build_graph(self) -> Any:
        """Return an uncompiled LangGraph StateGraph."""

    @property
    def graph(self) -> Any:
        return self._graph

    @staticmethod
    def thread_config(thread_id: str) -> RunnableConfig:
        """Build the stable cursor required by persistent checkpoints."""

        if not thread_id.strip():
            raise ValueError("thread_id is required")
        return {"configurable": {"thread_id": thread_id}}

    def invoke(
        self,
        state: StateT,
        *,
        config: RunnableConfig | None = None,
    ) -> dict[str, Any]:
        return self._graph.invoke(state, config=config)

    async def ainvoke(
        self,
        state: StateT,
        *,
        config: RunnableConfig | None = None,
    ) -> dict[str, Any]:
        return await self._graph.ainvoke(state, config=config)
