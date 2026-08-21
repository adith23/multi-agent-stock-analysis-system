from __future__ import annotations

from dataclasses import asdict
from typing import Any

from langchain_core.tools import tool

from engines.position_sizing.fixed_fractional_sizer import FixedFractionalSizer
from engines.position_sizing.kelly_sizer import KellySizer
from engines.position_sizing.risk_parity_sizer import RiskParitySizer
from engines.position_sizing.volatility_target_sizer import VolatilityTargetSizer


@tool
def compute_position_size(methodology: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Run a configured position-sizing Strategy implementation."""

    values = dict(inputs)
    if methodology == "kelly":
        strategy = KellySizer(
            win_probability=float(values.pop("win_probability")),
            payoff_ratio=float(values.pop("payoff_ratio")),
            fraction=float(values.pop("kelly_fraction", 0.5)),
        )
    elif methodology == "volatility_target":
        strategy = VolatilityTargetSizer(
            target_volatility=float(values.pop("target_volatility", 0.10))
        )
    elif methodology == "risk_parity":
        strategy = RiskParitySizer()
    elif methodology == "fixed_fractional":
        strategy = FixedFractionalSizer(fraction=float(values.pop("fraction", 0.02)))
    else:
        raise ValueError(f"unknown sizing methodology: {methodology}")
    return {key: str(value) for key, value in asdict(strategy.calculate_size(**values)).items()}
