from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.scenario.scenario_engine import ScenarioEngine


@tool
def run_premortem(scenario_inputs: dict[str, Any]) -> dict[str, Any]:
    """Run a deterministic adverse factor and idiosyncratic scenario."""

    return ScenarioEngine().compute(scenario_inputs)
