from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.exit_strategy.profit_target_engine import ProfitTargetEngine
from engines.exit_strategy.stop_loss_engine import StopLossEngine
from engines.exit_strategy.trailing_stop_engine import TrailingStopEngine


@tool
def generate_exit_strategy(inputs: dict[str, Any]) -> dict[str, Any]:
    """Generate protective stops, profit targets, and optional trailing stops."""

    stop = StopLossEngine().compute(inputs)
    targets = ProfitTargetEngine().compute(
        {
            "entry_price": inputs["entry_price"],
            "stop_price": stop["recommended_stop"],
            "r_multiples": inputs.get("r_multiples", (1, 2, 3)),
        }
    )
    trailing = (
        TrailingStopEngine().compute(inputs)
        if inputs.get("highest_price") and inputs.get("current_price")
        else {}
    )
    return {"stop": stop, "profit_targets": targets, "trailing": trailing}
