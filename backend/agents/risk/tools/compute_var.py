from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.risk.var_engine import ValueAtRiskEngine


@tool
def compute_var(var_inputs: dict[str, Any]) -> dict[str, Any]:
    """Compute parametric, historical, Monte Carlo VaR, and CVaR."""

    return ValueAtRiskEngine().compute(var_inputs)
