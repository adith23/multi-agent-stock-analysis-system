from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction

from agents.pm.tools.compute_position_size import compute_position_size
from agents.pm.tools.generate_exit_strategy import generate_exit_strategy
from agents.pm.tools.run_portfolio_optimization import run_portfolio_optimization
from apps.orchestrator.models import AnalysisRun
from engines.portfolio_optimization.rebalance_engine import RebalanceEngine

from ..models import (
    ExitStrategyPackage,
    PMRecommendation,
    PortfolioConstructionOutput,
    PositionSizingRecommendation,
)


class PortfolioService:
    @transaction.atomic
    def create_sizing(
        self,
        run: AnalysisRun,
        *,
        methodology: str,
        inputs: dict[str, Any],
    ) -> PositionSizingRecommendation:
        result = compute_position_size.invoke({"methodology": methodology, "inputs": inputs})
        return PositionSizingRecommendation.objects.update_or_create(
            analysis_run=run,
            defaults={
                "methodology": result["methodology"],
                "portfolio_weight_pct": Decimal(result["portfolio_weight_pct"]),
                "num_shares": int(result["num_shares"]),
                "dollar_amount": Decimal(result["dollar_amount"]),
                "entry_tranches": int(result["entry_tranches"]),
                "risk_budget_contribution": Decimal(result["risk_budget_contribution"]),
                "incremental_risk": inputs.get("incremental_risk", {}),
                "assumptions": inputs,
            },
        )[0]

    @transaction.atomic
    def create_no_position_sizing(
        self,
        run: AnalysisRun,
        *,
        reason: str,
        inputs: dict[str, Any],
    ) -> PositionSizingRecommendation:
        """Persist the only valid position size after a binding no-trade gate."""

        return PositionSizingRecommendation.objects.update_or_create(
            analysis_run=run,
            defaults={
                "methodology": "binding_gate_no_position",
                "portfolio_weight_pct": Decimal("0"),
                "num_shares": 0,
                "dollar_amount": Decimal("0"),
                "entry_tranches": 1,
                "risk_budget_contribution": Decimal("0"),
                "incremental_risk": {},
                "assumptions": {**inputs, "binding_gate": reason},
            },
        )[0]

    @transaction.atomic
    def create_exit_package(
        self,
        run: AnalysisRun,
        *,
        inputs: dict[str, Any],
    ) -> ExitStrategyPackage:
        result = generate_exit_strategy.invoke({"inputs": inputs})
        stop = result["stop"]
        return ExitStrategyPackage.objects.update_or_create(
            analysis_run=run,
            defaults={
                "entry_price": Decimal(str(inputs["entry_price"])),
                "stop_loss_price": Decimal(str(stop["recommended_stop"])),
                "stop_loss_pct": stop["stop_loss_pct"],
                "profit_targets": result["profit_targets"]["targets"],
                "trailing_stop": result["trailing"],
                "thesis_invalidation_triggers": inputs.get(
                    "thesis_invalidation_triggers",
                    ["Material thesis deterioration"],
                ),
                "time_based_review_date": inputs["time_based_review_date"],
            },
        )[0]

    @transaction.atomic
    def optimize(
        self,
        run: AnalysisRun,
        *,
        inputs: dict[str, Any],
    ) -> PortfolioConstructionOutput:
        target = run_portfolio_optimization.invoke(inputs)
        current = inputs.get("current_weights", {asset: 0.0 for asset in target})
        rebalance = RebalanceEngine().compute(
            {
                "current_weights": current,
                "target_weights": target,
                "portfolio_value": inputs.get("portfolio_value", 0),
                "drift_threshold": inputs.get("drift_threshold", 0.02),
            }
        )
        return PortfolioConstructionOutput.objects.update_or_create(
            analysis_run=run,
            defaults={
                "methodology": inputs["methodology"],
                "target_allocations": target,
                "current_allocations": current,
                "constraints": inputs["constraints"],
                "expected_metrics": inputs.get("expected_metrics", {}),
                "rebalance_required": rebalance["rebalance_required"],
                "rebalance_trades": rebalance["trades"],
            },
        )[0]

    @transaction.atomic
    def hold_current_allocations(
        self,
        run: AnalysisRun,
        *,
        inputs: dict[str, Any],
        reason: str,
    ) -> PortfolioConstructionOutput:
        """Persist a no-trade construction result after a binding approval gate."""

        current = inputs.get(
            "current_weights",
            {run.ticker.symbol: 0.0},
        )
        return PortfolioConstructionOutput.objects.update_or_create(
            analysis_run=run,
            defaults={
                "methodology": "binding_gate_no_trade",
                "target_allocations": current,
                "current_allocations": current,
                "constraints": inputs.get("constraints", {}),
                "expected_metrics": {"binding_gate": reason},
                "rebalance_required": False,
                "rebalance_trades": [],
            },
        )[0]

    @transaction.atomic
    def persist_recommendation(
        self,
        run: AnalysisRun,
        output: dict[str, Any],
    ) -> PMRecommendation:
        metadata = output.get("metadata", {})
        return PMRecommendation.objects.update_or_create(
            analysis_run=run,
            defaults={
                "ticker": run.ticker,
                "action": output["action"],
                "conviction": output["conviction"],
                "status": output.get("decision_status", "pending_review"),
                "summary": output["summary"],
                "rationale": output["rationale"],
                "expected_return": output.get("expected_return", {}),
                "position_size": output.get("position_size", {}),
                "entry_plan": output.get("entry_plan", []),
                "exit_conditions": output.get("exit_conditions", {}),
                "time_horizon": output["time_horizon"],
                "catalysts": output.get("catalysts", []),
                "portfolio_fit": output["portfolio_fit"],
                "capital_allocation_guidance": output["capital_allocation_guidance"],
                "conditions_precedent": output.get("conditions_precedent", []),
                "evidence": output.get("evidence", []),
                "assumptions": output.get("assumptions", []),
                "limitations": output.get("limitations", []),
                "agent_version": metadata.get("agent_version", ""),
                "model_version": metadata.get("model_name", ""),
                "prompt_version": metadata.get("prompt_version", ""),
            },
        )[0]
