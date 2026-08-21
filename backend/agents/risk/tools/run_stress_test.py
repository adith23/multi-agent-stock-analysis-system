from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.risk.stress_test_engine import StressTestEngine


@tool
def run_stress_test(stress_inputs: dict[str, Any]) -> dict[str, Any]:
    """Apply configured asset and factor stress scenarios."""

    return StressTestEngine().compute(stress_inputs)
