"""Thread-safe abstract factory for agent graph construction."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from apps.core.domain.exceptions import RegistryError

AgentFactory = Callable[..., Any]


class AgentRegistry:
    _factories: dict[str, AgentFactory] = {}
    _lock = threading.RLock()

    @classmethod
    def register(
        cls,
        agent_id: str,
        factory: AgentFactory,
        *,
        replace: bool = False,
    ) -> None:
        key = agent_id.strip().casefold()
        if not key:
            raise RegistryError("agent_id is required")
        with cls._lock:
            if key in cls._factories and not replace:
                raise RegistryError(f"agent '{agent_id}' is already registered")
            cls._factories[key] = factory

    @classmethod
    def create(cls, agent_id: str, **kwargs: Any) -> Any:
        key = agent_id.strip().casefold()
        with cls._lock:
            factory = cls._factories.get(key)
        if factory is None:
            raise RegistryError(f"unknown agent '{agent_id}'")
        return factory(**kwargs)

    @classmethod
    def available(cls) -> tuple[str, ...]:
        with cls._lock:
            return tuple(sorted(cls._factories))

    @classmethod
    def clear(cls) -> None:
        """Test-only reset hook."""

        with cls._lock:
            cls._factories.clear()


def register_default_agents() -> None:
    """Register every concrete graph lazily to avoid import-time model creation."""

    from agents.adversarial.graph import build_adversarial_agent_graph
    from agents.fundamental.graph import build_fundamental_agent_graph
    from agents.macro.graph import build_macro_agent_graph
    from agents.pm.graph import build_pm_agent_graph
    from agents.risk.graph import build_risk_agent_graph
    from agents.sentiment.graph import build_sentiment_agent_graph
    from agents.supervisor.graph import build_supervisor_graph
    from agents.technical.graph import build_technical_agent_graph

    factories = {
        "macro": build_macro_agent_graph,
        "fundamental": build_fundamental_agent_graph,
        "technical": build_technical_agent_graph,
        "sentiment": build_sentiment_agent_graph,
        "adversarial": build_adversarial_agent_graph,
        "risk": build_risk_agent_graph,
        "pm": build_pm_agent_graph,
        "supervisor": build_supervisor_graph,
    }
    for agent_id, factory in factories.items():
        AgentRegistry.register(agent_id, factory, replace=True)
