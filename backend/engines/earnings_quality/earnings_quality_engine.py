from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class EarningsQualityEngine(DeterministicEngine):
    """Beneish M-Score, Altman Z-Score, and accrual-quality screen."""

    REQUIRED = (
        "receivables_t",
        "revenue_t",
        "receivables_t1",
        "revenue_t1",
        "cogs_t",
        "cogs_t1",
        "current_assets_t",
        "current_assets_t1",
        "ppe_t",
        "ppe_t1",
        "total_assets_t",
        "total_assets_t1",
        "depreciation_t",
        "depreciation_t1",
        "sga_t",
        "sga_t1",
        "long_term_debt_t",
        "long_term_debt_t1",
        "current_liabilities_t",
        "current_liabilities_t1",
        "net_income_t",
        "cfo_t",
        "retained_earnings_t",
        "ebit_t",
        "market_cap_t",
        "total_liabilities_t",
    )

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, *self.REQUIRED)
        if (
            min(
                float(inputs["revenue_t"]),
                float(inputs["revenue_t1"]),
                float(inputs["total_assets_t"]),
                float(inputs["total_assets_t1"]),
            )
            <= 0
        ):
            raise EngineInputError("revenues and total assets must be positive")
        beneish = self._beneish(inputs)
        altman = self._altman(inputs)
        accrual = self.safe_divide(
            float(inputs["net_income_t"]) - float(inputs["cfo_t"]),
            float(inputs["total_assets_t"]),
        )
        flags: list[str] = []
        if beneish["manipulation_likely"]:
            flags.append("beneish_manipulation_risk")
        if altman["zone"] != "safe":
            flags.append(f"altman_{altman['zone']}")
        if abs(accrual) > 0.10:
            flags.append("high_accruals")
        flags.extend(str(flag) for flag in inputs.get("qualitative_flags", []))
        score = max(0.0, 100.0 - len(flags) * 20)
        return {
            "beneish": beneish,
            "altman": altman,
            "accrual_ratio": round(accrual, 6),
            "high_accruals": abs(accrual) > 0.10,
            "red_flags": flags,
            "quality_score": score,
            "engine_version": self.engine_version,
        }

    def _beneish(self, data: dict[str, Any]) -> dict[str, Any]:
        def f(key: str) -> float:
            return float(data[key])

        dsri = (f("receivables_t") / f("revenue_t")) / (f("receivables_t1") / f("revenue_t1"))
        gm_t = (f("revenue_t") - f("cogs_t")) / f("revenue_t")
        gm_t1 = (f("revenue_t1") - f("cogs_t1")) / f("revenue_t1")
        gmi = self.safe_divide(gm_t1, gm_t, default=1)
        aqi_t = 1 - (f("current_assets_t") + f("ppe_t")) / f("total_assets_t")
        aqi_t1 = 1 - (f("current_assets_t1") + f("ppe_t1")) / f("total_assets_t1")
        aqi = self.safe_divide(aqi_t, aqi_t1, default=1)
        sgi = f("revenue_t") / f("revenue_t1")
        dep_t = self.safe_divide(f("depreciation_t"), f("depreciation_t") + f("ppe_t"))
        dep_t1 = self.safe_divide(f("depreciation_t1"), f("depreciation_t1") + f("ppe_t1"))
        depi = self.safe_divide(dep_t1, dep_t, default=1)
        sgai = self.safe_divide(f("sga_t"), f("revenue_t")) / self.safe_divide(
            f("sga_t1"), f("revenue_t1"), default=1
        )
        lev_t = (f("long_term_debt_t") + f("current_liabilities_t")) / f("total_assets_t")
        lev_t1 = (f("long_term_debt_t1") + f("current_liabilities_t1")) / f("total_assets_t1")
        lvgi = self.safe_divide(lev_t, lev_t1, default=1)
        tata = (f("net_income_t") - f("cfo_t")) / f("total_assets_t")
        score = (
            -4.84
            + 0.920 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            + 0.115 * depi
            - 0.172 * sgai
            + 4.679 * tata
            - 0.327 * lvgi
        )
        return {
            "m_score": round(score, 6),
            "manipulation_likely": score > -1.78,
            "components": {
                key: round(value, 6)
                for key, value in {
                    "dsri": dsri,
                    "gmi": gmi,
                    "aqi": aqi,
                    "sgi": sgi,
                    "depi": depi,
                    "sgai": sgai,
                    "lvgi": lvgi,
                    "tata": tata,
                }.items()
            },
        }

    def _altman(self, data: dict[str, Any]) -> dict[str, Any]:
        def f(key: str) -> float:
            return float(data[key])

        assets = f("total_assets_t")
        components = {
            "working_capital_ratio": (f("current_assets_t") - f("current_liabilities_t")) / assets,
            "retained_earnings_ratio": f("retained_earnings_t") / assets,
            "ebit_ratio": f("ebit_t") / assets,
            "market_equity_ratio": self.safe_divide(f("market_cap_t"), f("total_liabilities_t")),
            "asset_turnover": f("revenue_t") / assets,
        }
        score = (
            1.2 * components["working_capital_ratio"]
            + 1.4 * components["retained_earnings_ratio"]
            + 3.3 * components["ebit_ratio"]
            + 0.6 * components["market_equity_ratio"]
            + components["asset_turnover"]
        )
        zone = "safe" if score > 2.99 else ("grey" if score > 1.81 else "distress")
        return {
            "z_score": round(score, 6),
            "zone": zone,
            "components": {key: round(value, 6) for key, value in components.items()},
        }
