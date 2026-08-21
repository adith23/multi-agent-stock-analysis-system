"""Read repository for canonical market-data projections."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.market_data.models import (
    CompanyProfile,
    FinancialStatement,
    MacroIndicator,
    NewsItem,
    OHLCVBar,
)


class MarketDataRepository:
    def macro_observations(
        self,
        series_ids: list[str],
        *,
        per_series_limit: int = 24,
        as_of=None,
    ) -> list[dict[str, Any]]:
        queryset = MacroIndicator.objects.filter(series_id__in=series_ids)
        if as_of is not None:
            queryset = queryset.filter(
                observed_at__lte=as_of.date(),
                available_at__lte=as_of,
            )
        rows = queryset.order_by("series_id", "-observed_at").values(
            "series_id",
            "title",
            "observed_at",
            "value",
            "frequency",
            "unit",
            "source_id",
        )
        counts: dict[str, int] = {}
        result = []
        for row in rows.iterator():
            series_id = str(row["series_id"])
            counts[series_id] = counts.get(series_id, 0) + 1
            if counts[series_id] <= per_series_limit:
                result.append(row)
        return result

    def financial_statements(
        self,
        ticker: str,
        *,
        limit: int = 12,
        as_of=None,
    ) -> list[dict[str, Any]]:
        queryset = FinancialStatement.objects.filter(ticker__symbol=ticker.upper())
        if as_of is not None:
            queryset = queryset.filter(
                period_end__lte=as_of.date(),
                available_at__lte=as_of,
            )
        return list(
            queryset.order_by("-period_end").values(
                "statement_type",
                "period_end",
                "fiscal_year",
                "fiscal_quarter",
                "currency",
                "values",
                "source_id",
                "source_timestamp",
            )[:limit]
        )

    def company_profile(self, ticker: str, *, as_of=None) -> dict[str, Any]:
        queryset = CompanyProfile.objects.filter(ticker__symbol=ticker.upper())
        if as_of is not None:
            queryset = queryset.filter(available_at__lte=as_of)
        return (
            queryset.values(
                "legal_name",
                "description",
                "website",
                "headquarters_country",
                "market_cap",
                "shares_outstanding",
                "attributes",
                "source_id",
            ).first()
            or {}
        )

    def price_bars(
        self,
        ticker: str,
        *,
        interval: str = "1d",
        limit: int = 252,
        as_of=None,
    ) -> list[dict[str, Any]]:
        queryset = OHLCVBar.objects.filter(
            ticker__symbol=ticker.upper(),
            interval=interval,
        )
        if as_of is not None:
            queryset = queryset.filter(timestamp__lte=as_of, available_at__lte=as_of)
        rows = list(
            queryset.order_by("-timestamp").values(
                "timestamp", "open", "high", "low", "close", "volume", "source_id"
            )[:limit]
        )
        return list(reversed(rows))

    def news(
        self,
        ticker: str,
        *,
        lookback_days: int = 30,
        limit: int = 100,
        as_of=None,
    ) -> list[dict[str, Any]]:
        as_of = as_of or timezone.now()
        return list(
            NewsItem.objects.filter(
                ticker__symbol=ticker.upper(),
                published_at__gte=as_of - timedelta(days=lookback_days),
                published_at__lte=as_of,
                available_at__lte=as_of,
            )
            .order_by("-published_at")
            .values(
                "headline",
                "summary",
                "url",
                "publisher",
                "published_at",
                "sentiment_score",
                "categories",
                "source_id",
            )[:limit]
        )
