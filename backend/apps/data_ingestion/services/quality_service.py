from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.data_ingestion.domain import DataCategory, NormalizedRecordData, QualityAssessment


class DataQualityService:
    """Deterministic completeness, validity, and freshness checks."""

    REQUIRED_FIELDS = {
        DataCategory.QUOTE: ("symbol", "timestamp", "price"),
        DataCategory.OHLCV: (
            "symbol",
            "timestamp",
            "interval",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ),
        DataCategory.FILING: ("symbol", "form"),
        DataCategory.MACRO: ("series_id", "observed_at", "value"),
        DataCategory.NEWS: ("headline", "published_at"),
        DataCategory.INSIDER_TRANSACTION: ("symbol", "owner_name", "transaction_date"),
    }
    MAX_AGE = {
        DataCategory.QUOTE: timedelta(minutes=30),
        DataCategory.OHLCV: timedelta(days=10),
        DataCategory.NEWS: timedelta(days=30),
        DataCategory.MACRO: timedelta(days=120),
        DataCategory.FILING: timedelta(days=550),
    }

    def assess(
        self,
        record: NormalizedRecordData,
        *,
        now: datetime | None = None,
    ) -> QualityAssessment:
        current_time = now or datetime.now(UTC)
        category = DataCategory(record.category)
        issues: list[str] = []
        required = self.REQUIRED_FIELDS.get(category, ())
        missing = [field for field in required if record.payload.get(field) in (None, "", [], {})]
        if missing:
            issues.append(f"missing_required_fields:{','.join(missing)}")

        malformed = False
        if category == DataCategory.OHLCV and not missing:
            malformed = (
                float(record.payload["high"]) < float(record.payload["low"])
                or min(
                    float(record.payload["open"]),
                    float(record.payload["high"]),
                    float(record.payload["low"]),
                    float(record.payload["close"]),
                    float(record.payload["volume"]),
                )
                < 0
            )
            if malformed:
                issues.append("invalid_ohlcv_range")

        stale = False
        max_age = self.MAX_AGE.get(category)
        if max_age and record.source_timestamp:
            stale = current_time - record.source_timestamp > max_age
            if stale:
                issues.append("stale")

        score = 1.0
        if required:
            score -= 0.6 * (len(missing) / len(required))
        if malformed:
            score -= 0.4
        if stale:
            score -= 0.15
        score = round(max(0.0, min(1.0, score)), 4)
        return QualityAssessment(
            score=score,
            is_acceptable=not malformed and not missing and score >= 0.6,
            issues=tuple(issues),
            flags={
                "missing": bool(missing),
                "malformed": malformed,
                "stale": stale,
                "source_unavailable": False,
                "schema_conflict": False,
            },
        )
