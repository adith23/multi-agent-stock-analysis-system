"""Abstract boundaries for replaceable infrastructure and domain strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from .value_objects import PositionSize


class IDataConnector(ABC):
    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def fetch(self, symbol: str, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    @property
    @abstractmethod
    def source_type(self) -> str: ...


class IAgentGraph(ABC):
    @abstractmethod
    def invoke(self, state: Mapping[str, Any], **kwargs: Any) -> Mapping[str, Any]: ...

    @property
    @abstractmethod
    def agent_id(self) -> str: ...

    @property
    @abstractmethod
    def agent_version(self) -> str: ...


class IAgentService(IAgentGraph):
    @abstractmethod
    def analyze(self, context: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_stance(self) -> str: ...


class ISizingStrategy(ABC):
    @abstractmethod
    def calculate_size(
        self,
        conviction: float,
        volatility: float,
        liquidity: float,
        correlation: float,
        risk_budget: float,
        portfolio_value: float,
    ) -> PositionSize: ...

    @property
    @abstractmethod
    def methodology_name(self) -> str: ...


class IOptimizationStrategy(ABC):
    @abstractmethod
    def optimize(
        self,
        expected_returns: Any,
        covariance_matrix: Any,
        constraints: dict[str, Any],
    ) -> dict[str, float]: ...


class IDeterministicEngine(ABC):
    @abstractmethod
    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]: ...

    @property
    @abstractmethod
    def engine_version(self) -> str: ...


class IRuleEngine(ABC):
    @abstractmethod
    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_rules(self) -> list[dict[str, Any]]: ...
