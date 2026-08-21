from __future__ import annotations

import math

from rest_framework import serializers

from apps.api.validators import validate_bounded_json
from apps.portfolio.models import (
    PerformanceAttributionRecord,
    ScenarioAnalysisResult,
)
from apps.research.models import CatalystRecord
from apps.risk_compliance.models import PortfolioState


class PortfolioStateSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source="owner.username", allow_null=True, read_only=True)

    class Meta:
        model = PortfolioState
        fields = (
            "id",
            "portfolio_code",
            "name",
            "owner",
            "as_of",
            "base_currency",
            "total_value",
            "holdings",
            "weights",
            "sector_exposures",
            "factor_exposures",
            "liquidity_metrics",
            "risk_metrics",
            "gross_leverage",
            "version",
            "created_at",
        )


class PortfolioRiskSerializer(serializers.Serializer):
    portfolio_code = serializers.CharField()
    as_of = serializers.DateTimeField()
    gross_leverage = serializers.FloatField()
    sector_exposures = serializers.DictField()
    factor_exposures = serializers.DictField()
    liquidity_metrics = serializers.DictField()
    risk_metrics = serializers.DictField()


class ScenarioRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, trim_whitespace=True)
    positions = serializers.DictField(child=serializers.FloatField())
    factor_exposures = serializers.DictField()
    factor_shocks = serializers.DictField(child=serializers.FloatField())
    asset_shocks = serializers.DictField(
        child=serializers.FloatField(),
        required=False,
        default=dict,
    )
    portfolio_code = serializers.CharField(max_length=64, required=False)
    analysis_run_id = serializers.UUIDField(required=False)

    def validate_positions(self, value: dict) -> dict:
        if len(value) > 200:
            raise serializers.ValidationError("At most 200 positions are allowed.")
        if not value or any(
            not str(key).strip() or not math.isfinite(float(amount)) or float(amount) <= 0
            for key, amount in value.items()
        ):
            raise serializers.ValidationError(
                "Positions require non-empty symbols and finite positive values."
            )
        return {str(key).strip().upper(): float(amount) for key, amount in value.items()}

    def validate_factor_shocks(self, value: dict) -> dict:
        if len(value) > 100:
            raise serializers.ValidationError("At most 100 factor shocks are allowed.")
        if not value or any(
            not math.isfinite(float(shock)) or not -1.0 <= float(shock) <= 5.0
            for shock in value.values()
        ):
            raise serializers.ValidationError(
                "Factor shocks must be finite values between -1.0 and 5.0."
            )
        return value

    def validate_factor_exposures(self, value: dict) -> dict:
        return validate_bounded_json(value, field_name="factor_exposures")

    def validate_asset_shocks(self, value: dict) -> dict:
        if len(value) > 200:
            raise serializers.ValidationError("At most 200 asset shocks are allowed.")
        if any(
            not math.isfinite(float(shock)) or not -1.0 <= float(shock) <= 5.0
            for shock in value.values()
        ):
            raise serializers.ValidationError(
                "Asset shocks must be finite values between -1.0 and 5.0."
            )
        return value

    def validate(self, attrs):
        positions = set(attrs["positions"])
        exposure_assets = set(attrs["factor_exposures"])
        if not positions.issubset(exposure_assets):
            missing = sorted(positions - exposure_assets)
            raise serializers.ValidationError(
                {"factor_exposures": f"Missing exposure rows for: {', '.join(missing)}"}
            )
        unknown_shocks = set(attrs["asset_shocks"]) - positions
        if unknown_shocks:
            raise serializers.ValidationError(
                {"asset_shocks": f"Unknown position symbols: {', '.join(sorted(unknown_shocks))}"}
            )
        return attrs


class ScenarioResultSerializer(serializers.ModelSerializer):
    initiated_by = serializers.CharField(
        source="initiated_by.username",
        allow_null=True,
        read_only=True,
    )

    class Meta:
        model = ScenarioAnalysisResult
        fields = (
            "id",
            "name",
            "scenario_type",
            "inputs",
            "results",
            "worst_impact",
            "initiated_by",
            "created_at",
        )


class PerformanceAttributionSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="recommendation.ticker.symbol", read_only=True)
    action = serializers.CharField(source="recommendation.action", read_only=True)

    class Meta:
        model = PerformanceAttributionRecord
        fields = (
            "id",
            "symbol",
            "action",
            "measurement_period",
            "period_start",
            "period_end",
            "entry_price",
            "exit_price",
            "realized_return",
            "benchmark_return",
            "excess_return",
            "hit",
            "risk_adjusted_return",
            "agent_attribution",
            "signal_decay",
            "version",
        )


class PerformanceResponseSerializer(serializers.Serializer):
    summary = serializers.DictField()
    records = PerformanceAttributionSerializer(many=True)


class CatalystSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="ticker.symbol", read_only=True)

    class Meta:
        model = CatalystRecord
        fields = (
            "id",
            "symbol",
            "title",
            "description",
            "catalyst_type",
            "expected_at",
            "actual_at",
            "direction",
            "probability",
            "impact",
            "evidence",
            "is_active",
            "is_thesis_critical",
            "outcome_status",
            "outcome_notes",
            "last_checked_at",
            "version",
        )


class AlertSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = serializers.ChoiceField(
        choices=("regime_transition", "exit_trigger", "catalyst_delayed")
    )
    severity = serializers.ChoiceField(choices=("info", "warning", "critical"))
    detected_at = serializers.DateTimeField()
    symbol = serializers.CharField(allow_null=True)
    title = serializers.CharField()
    details = serializers.DictField()
