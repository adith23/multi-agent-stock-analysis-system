from __future__ import annotations

import json
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder

from apps.market_data.repositories import MarketDataRepository
from apps.orchestrator.models import AnalysisRun
from apps.risk_compliance.repositories import RiskComplianceRepository
from apps.signals.models import RegimeState


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


class AgentInputBuilder:
    """Build processed agent inputs from canonical repositories and run overrides."""

    def __init__(
        self,
        market_repository: MarketDataRepository | None = None,
        risk_repository: RiskComplianceRepository | None = None,
    ) -> None:
        self.market = market_repository or MarketDataRepository()
        self.risk = risk_repository or RiskComplianceRepository()

    def build(self, run: AnalysisRun, agent_id: str) -> dict[str, Any]:
        overrides = run.analysis_config.get("agent_inputs", {}).get(agent_id)
        if overrides is not None:
            return _json_safe(overrides)
        method = getattr(self, f"_build_{agent_id}")
        return _json_safe(method(run))

    def _build_macro(self, run: AnalysisRun) -> dict[str, Any]:
        series = run.analysis_config.get(
            "macro_series",
            ["FEDFUNDS", "CPIAUCSL", "GDPC1", "UNRATE", "DGS10", "DGS2", "VIXCLS"],
        )
        current = (
            RegimeState.objects.filter(as_of__lte=run.data_cutoff_at).order_by("-as_of").first()
        )
        return {
            "macro_indicators": self.market.macro_observations(
                series,
                as_of=run.data_cutoff_at,
                available_as_of=run.knowledge_cutoff_at,
                source_types=self._sources(run, "macro"),
            ),
            "regime_output": {
                "regime": current.regime if current else "unknown",
                "probability": current.probability if current else 0.0,
            },
        }

    def _build_fundamental(self, run: AnalysisRun) -> dict[str, Any]:
        return {
            "financials": {
                "statements": self.market.financial_statements(
                    run.ticker,
                    as_of=run.data_cutoff_at,
                    available_as_of=run.knowledge_cutoff_at,
                    source_types=self._sources(run, "financial_statement"),
                ),
            },
            "company_profile": self.market.company_profile(
                run.ticker,
                as_of=run.data_cutoff_at,
                available_as_of=run.knowledge_cutoff_at,
                source_types=self._sources(run, "company_profile"),
            ),
            "macro_context": self._build_macro(run),
        }

    def _build_technical(self, run: AnalysisRun) -> dict[str, Any]:
        return {
            "ohlcv": self.market.price_bars(
                run.ticker,
                as_of=run.data_cutoff_at,
                available_as_of=run.knowledge_cutoff_at,
                source_types=self._sources(run, "ohlcv"),
            ),
            "benchmark_prices": run.analysis_config.get("benchmark_prices", []),
        }

    def _build_sentiment(self, run: AnalysisRun) -> dict[str, Any]:
        news = self.market.news(
            run.ticker,
            as_of=run.data_cutoff_at,
            available_as_of=run.knowledge_cutoff_at,
            source_types=self._sources(run, "news"),
        )
        return {
            "news": news,
            "texts": [
                f"{item.get('headline', '')}. {item.get('summary', '')}".strip() for item in news
            ],
            "article_counts": run.analysis_config.get("article_counts", []),
        }

    def _build_risk(self, run: AnalysisRun) -> dict[str, Any]:
        portfolio = self.risk.latest_portfolio(
            run.analysis_config.get("portfolio_code"),
            as_of=run.data_cutoff_at,
        )
        state = (
            {
                "portfolio_code": portfolio.portfolio_code,
                "total_value": portfolio.total_value,
                "sector_exposures": portfolio.sector_exposures,
                "factor_exposures": portfolio.factor_exposures,
                "liquidity_metrics": portfolio.liquidity_metrics,
                "risk_metrics": portfolio.risk_metrics,
            }
            if portfolio
            else {}
        )
        metrics = dict(run.analysis_config.get("risk_metrics", {}))
        if portfolio:
            metrics.setdefault("gross_leverage", portfolio.gross_leverage)
        return {
            "proposed_trade": run.analysis_config.get("proposed_trade", {}),
            "portfolio_state": state,
            "limit_metrics": metrics or {"position_weight": 0.0},
        }

    def _build_pm(self, run: AnalysisRun) -> dict[str, Any]:
        return {
            "conviction": {},
            "compliance": {},
            "mandate": run.analysis_config.get("mandate", {}),
            "catalyst_events": run.analysis_config.get("catalysts", []),
        }

    @staticmethod
    def _sources(run: AnalysisRun, category: str) -> list[str] | None:
        try:
            values = run.data_preparation.selected_sources.get(category, [])
        except AttributeError:
            return None
        return list(values) or None
