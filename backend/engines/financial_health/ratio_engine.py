from __future__ import annotations

from typing import Any

import numpy as np

from engines.base import DeterministicEngine


class FinancialRatioEngine(DeterministicEngine):
    """Profitability, liquidity, leverage, cash conversion, and growth dashboard."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(
            inputs,
            "revenue",
            "gross_profit",
            "operating_income",
            "net_income",
            "cash_from_operations",
            "current_assets",
            "current_liabilities",
            "total_assets",
            "total_equity",
            "total_debt",
        )
        ratio = self.safe_divide
        revenue = float(inputs["revenue"])
        assets = float(inputs["total_assets"])
        equity = float(inputs["total_equity"])
        current_liabilities = float(inputs["current_liabilities"])
        debt = float(inputs["total_debt"])
        ebit = float(inputs.get("ebit", inputs["operating_income"]))
        interest = float(inputs.get("interest_expense", 0))
        ratios = {
            "gross_margin": ratio(float(inputs["gross_profit"]), revenue),
            "operating_margin": ratio(float(inputs["operating_income"]), revenue),
            "net_margin": ratio(float(inputs["net_income"]), revenue),
            "return_on_assets": ratio(float(inputs["net_income"]), assets),
            "return_on_equity": ratio(float(inputs["net_income"]), equity),
            "current_ratio": ratio(float(inputs["current_assets"]), current_liabilities),
            "quick_ratio": ratio(
                float(inputs["current_assets"]) - float(inputs.get("inventory", 0)),
                current_liabilities,
            ),
            "debt_to_equity": ratio(debt, equity),
            "debt_to_assets": ratio(debt, assets),
            "interest_coverage": ratio(ebit, interest, default=float("inf")),
            "cash_conversion": ratio(
                float(inputs["cash_from_operations"]), float(inputs["net_income"])
            ),
            "asset_turnover": ratio(revenue, assets),
        }
        if inputs.get("previous_revenue") is not None:
            ratios["revenue_growth"] = ratio(
                revenue - float(inputs["previous_revenue"]),
                float(inputs["previous_revenue"]),
            )
        if inputs.get("previous_net_income") is not None:
            ratios["earnings_growth"] = ratio(
                float(inputs["net_income"]) - float(inputs["previous_net_income"]),
                abs(float(inputs["previous_net_income"])),
            )
        score_components = [
            np.clip(ratios["gross_margin"] / 0.4, 0, 1),
            np.clip(ratios["operating_margin"] / 0.2, 0, 1),
            np.clip(ratios["current_ratio"] / 2, 0, 1),
            np.clip(1 - ratios["debt_to_assets"], 0, 1),
            np.clip(ratios["cash_conversion"], 0, 1),
        ]
        serializable = {
            key: ("unbounded" if np.isinf(value) else round(float(value), 6))
            for key, value in ratios.items()
        }
        return {
            "ratios": serializable,
            "health_score": round(float(np.mean(score_components) * 100), 2),
            "engine_version": self.engine_version,
        }
