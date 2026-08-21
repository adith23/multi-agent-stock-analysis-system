"""Read repository for regime and technical-signal memory."""

from __future__ import annotations

from typing import Any

from apps.signals.models import RegimeState, TechnicalSignal


class SignalRepository:
    def recent_regimes(self, *, limit: int = 5) -> list[dict[str, Any]]:
        return list(
            RegimeState.objects.order_by("-as_of").values(
                "regime",
                "probability",
                "as_of",
                "indicators",
                "model_metadata",
            )[:limit]
        )

    def recent_technical_signals(
        self,
        ticker: str,
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return list(
            TechnicalSignal.objects.filter(ticker__symbol=ticker.upper())
            .order_by("-observed_at")
            .values(
                "signal_type",
                "timeframe",
                "observed_at",
                "value",
                "direction",
                "strength",
                "parameters",
            )[:limit]
        )
