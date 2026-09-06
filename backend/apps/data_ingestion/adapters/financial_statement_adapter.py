from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from apps.data_ingestion.domain import DataCategory, NormalizationError, NormalizedRecordData

from .base import BaseNormalizationAdapter


class FinancialStatementAdapter(BaseNormalizationAdapter):
    """Normalize provider financials into one canonical record per reporting period."""

    STATEMENT_TYPES = frozenset({"income", "balance_sheet", "cash_flow", "metrics"})
    STATEMENT_TYPE_ALIASES = {
        "balance": "balance_sheet",
        "balance_sheet": "balance_sheet",
        "balancesheet": "balance_sheet",
        "cash_flow": "cash_flow",
        "cashflow": "cash_flow",
        "financials": "income",
        "income": "income",
        "income_statement": "income",
        "metrics": "metrics",
    }

    def normalize(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        category: str,
        entity_identifier: str = "",
    ) -> list[NormalizedRecordData]:
        if category != DataCategory.FINANCIAL_STATEMENT:
            raise NormalizationError(
                f"FinancialStatementAdapter cannot normalize category {category!r}"
            )

        symbol = str(payload.get("symbol") or entity_identifier).strip().upper()
        if not symbol:
            raise NormalizationError("financial statement requires a symbol")

        if payload.get("period_end") or payload.get("periodEndDate"):
            return [self._canonical_record(payload, source_type=source_type, symbol=symbol)]
        if isinstance(payload.get("statement"), Mapping):
            return self._normalize_tabular(payload, source_type=source_type, symbol=symbol)
        if isinstance(payload.get("series"), Mapping):
            return self._normalize_metric_series(payload, source_type=source_type, symbol=symbol)
        raise NormalizationError("unsupported financial-statement payload shape")

    def _normalize_tabular(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        symbol: str,
    ) -> list[NormalizedRecordData]:
        # Legacy Yahoo payloads wrapped ``ticker.financials`` without a type;
        # that endpoint is unambiguously the annual income statement.
        statement_type = self._statement_type(payload.get("statement_type") or "income")
        currency = self._currency(payload.get("currency"))
        statement = payload["statement"]
        records = []
        for period_value, period_values in statement.items():
            if not isinstance(period_values, Mapping):
                raise NormalizationError(
                    "financial statement periods must contain metric mappings"
                )
            period = self._period(period_value)
            values = {
                str(metric): value for metric, value in period_values.items() if value is not None
            }
            if not values:
                continue
            records.append(
                self._record(
                    source_type=source_type,
                    symbol=symbol,
                    statement_type=statement_type,
                    period=period,
                    currency=currency,
                    values=values,
                )
            )
        if not records:
            raise NormalizationError("financial statement contains no usable reporting periods")
        return sorted(records, key=lambda record: record.source_timestamp or datetime.min)

    def _normalize_metric_series(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        symbol: str,
    ) -> list[NormalizedRecordData]:
        series = payload["series"]
        # The model has no reporting-frequency dimension. Prefer annual data so a
        # fiscal year-end quarter cannot overwrite the annual observation.
        observations = series.get("annual") or series.get("quarterly")
        if not isinstance(observations, Mapping):
            raise NormalizationError("financial metric series contains no observations")

        values_by_period: dict[str, dict[str, Any]] = defaultdict(dict)
        for metric, metric_observations in observations.items():
            if not isinstance(metric_observations, list):
                continue
            for observation in metric_observations:
                if not isinstance(observation, Mapping) or not observation.get("period"):
                    continue
                value = observation.get("v", observation.get("value"))
                if value is not None:
                    values_by_period[str(observation["period"])][str(metric)] = value

        currency = self._currency(payload.get("currency"))
        records = [
            self._record(
                source_type=source_type,
                symbol=symbol,
                statement_type="metrics",
                period=self._period(period),
                currency=currency,
                values=values,
            )
            for period, values in values_by_period.items()
            if values
        ]
        if not records:
            raise NormalizationError("financial metric series contains no usable observations")
        return sorted(records, key=lambda record: record.source_timestamp or datetime.min)

    def _canonical_record(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        symbol: str,
    ) -> NormalizedRecordData:
        period = self._period(payload.get("period_end") or payload.get("periodEndDate"))
        values = payload.get("values")
        if not isinstance(values, Mapping) or not values:
            raise NormalizationError("financial statement requires non-empty values")
        return self._record(
            source_type=source_type,
            symbol=symbol,
            statement_type=self._statement_type(payload.get("statement_type")),
            period=period,
            currency=self._currency(payload.get("currency")),
            values=dict(values),
            fiscal_year=payload.get("fiscal_year"),
            fiscal_quarter=payload.get("fiscal_quarter"),
            accession_number=str(payload.get("accession_number") or ""),
        )

    def _record(
        self,
        *,
        source_type: str,
        symbol: str,
        statement_type: str,
        period: datetime,
        currency: str,
        values: dict[str, Any],
        fiscal_year: Any = None,
        fiscal_quarter: Any = None,
        accession_number: str = "",
    ) -> NormalizedRecordData:
        period_date = period.date()
        quarter = int(fiscal_quarter) if fiscal_quarter is not None else None
        if quarter is not None and quarter not in range(1, 5):
            raise NormalizationError("financial statement fiscal_quarter must be between 1 and 4")
        canonical = {
            "symbol": symbol,
            "statement_type": statement_type,
            "period_end": period_date.isoformat(),
            "fiscal_year": int(fiscal_year or period_date.year),
            "fiscal_quarter": quarter,
            "currency": currency,
            "accession_number": accession_number,
            "values": values,
        }
        source_id = f"{symbol}:{statement_type}:{period_date.isoformat()}"
        return NormalizedRecordData(
            category=DataCategory.FINANCIAL_STATEMENT,
            source_type=source_type,
            source_id=source_id,
            entity_identifier=symbol,
            source_timestamp=period,
            payload=canonical,
            canonical_key=f"financial_statement:{source_id}",
        )

    def _statement_type(self, value: Any) -> str:
        normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        statement_type = self.STATEMENT_TYPE_ALIASES.get(normalized)
        if statement_type not in self.STATEMENT_TYPES:
            raise NormalizationError(f"unsupported financial statement type: {value!r}")
        return statement_type

    @staticmethod
    def _currency(value: Any) -> str:
        currency = str(value or "USD").strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise NormalizationError(f"invalid financial statement currency: {value!r}")
        return currency

    def _period(self, value: Any) -> datetime:
        try:
            period = self.datetime(value)
        except (TypeError, ValueError) as exc:
            raise NormalizationError(f"invalid financial statement period: {value!r}") from exc
        if period is None:
            raise NormalizationError("financial statement requires a period_end")
        return period.astimezone(UTC)
