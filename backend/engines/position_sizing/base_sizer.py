from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from apps.core.domain.interfaces import ISizingStrategy
from apps.core.domain.value_objects import PositionSize
from engines.exceptions import EngineInputError


class SizingStrategy(ISizingStrategy, ABC):
    """Strategy-pattern base with shared caps and share conversion."""

    @property
    @abstractmethod
    def methodology_name(self) -> str: ...

    @abstractmethod
    def _weight(
        self,
        *,
        conviction: float,
        volatility: float,
        liquidity: float,
        correlation: float,
        risk_budget: float,
    ) -> float: ...

    def calculate_size(
        self,
        conviction: float,
        volatility: float,
        liquidity: float,
        correlation: float,
        risk_budget: float,
        portfolio_value: float,
        *,
        price: float = 1.0,
        maximum_weight: float = 0.10,
        entry_tranches: int = 1,
    ) -> PositionSize:
        if not 0 <= conviction <= 100 or volatility < 0 or portfolio_value < 0 or price <= 0:
            raise EngineInputError("invalid sizing inputs")
        raw = self._weight(
            conviction=conviction,
            volatility=volatility,
            liquidity=liquidity,
            correlation=correlation,
            risk_budget=risk_budget,
        )
        weight = max(0.0, min(raw, maximum_weight))
        amount = portfolio_value * weight
        return PositionSize(
            portfolio_weight_pct=Decimal(str(round(weight * 100, 6))),
            num_shares=int(amount // price),
            dollar_amount=Decimal(str(round(amount, 2))),
            methodology=self.methodology_name,
            entry_tranches=entry_tranches,
            risk_budget_contribution=Decimal(str(round(weight * max(volatility, 0), 8))),
        )
