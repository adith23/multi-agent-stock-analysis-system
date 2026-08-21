from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.valuation.dcf_engine import DCFEngine
from engines.valuation.multiples_engine import MultiplesValuationEngine


@tool
def run_valuation(
    dcf_inputs: dict[str, Any] | None = None,
    multiples_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run configured deterministic valuation methods and aggregate their outputs."""

    result: dict[str, Any] = {}
    if dcf_inputs:
        result["dcf"] = DCFEngine().compute(dcf_inputs)
    if multiples_inputs:
        result["multiples"] = MultiplesValuationEngine().compute(multiples_inputs)
    if not result:
        raise ValueError("at least one valuation input is required")
    return result
