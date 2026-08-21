from __future__ import annotations

import operator
from typing import Annotated, Any, NotRequired

from agents.base.state import AnalysisState


class SupervisorState(AnalysisState):
    agent_inputs: dict[str, dict[str, Any]]
    parallel_results: Annotated[list[dict[str, Any]], operator.add]
    adversarial_output: NotRequired[dict[str, Any]]
    risk_output: NotRequired[dict[str, Any]]
    pm_output: NotRequired[dict[str, Any]]
    human_decision: NotRequired[dict[str, Any]]
