from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.risk.concentration_engine import ConcentrationEngine


@tool
def check_concentration(concentration_inputs: dict[str, Any]) -> dict[str, Any]:
    """Compute position, sector, and HHI concentration diagnostics."""

    return ConcentrationEngine().compute(concentration_inputs)
