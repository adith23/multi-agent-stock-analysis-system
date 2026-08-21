from __future__ import annotations

from typing import Any

from engines.scenario.scenario_engine import ScenarioEngine

from ..models import ScenarioAnalysisResult


class ScenarioService:
    def run(
        self,
        *,
        name: str,
        inputs: dict[str, Any],
        user=None,
        analysis_run=None,
        portfolio_state=None,
    ) -> ScenarioAnalysisResult:
        result = ScenarioEngine().compute({"name": name, **inputs})
        return ScenarioAnalysisResult.objects.create(
            name=name,
            inputs=inputs,
            results=result,
            worst_impact=result["portfolio_return"],
            initiated_by=user,
            analysis_run=analysis_run,
            portfolio_state=portfolio_state,
        )
