from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.api.validators import validate_bounded_json
from apps.orchestrator.models import AnalysisRun, AnalysisScope, PipelineStepResult
from apps.portfolio.models import PMRecommendation
from apps.research.models import BullBearDecisionMemo, SpecialistReport
from apps.risk_compliance.models import ComplianceResult, RiskValidationResult
from apps.signals.models import ConvictionScorePackage, SignalAgreementMatrix


class AnalysisCreateSerializer(serializers.Serializer):
    ALLOWED_CONFIG_KEYS = frozenset(
        {
            "agent_inputs",
            "article_counts",
            "benchmark_prices",
            "catalysts",
            "compliance_context",
            "exit_inputs",
            "expected_return_high",
            "expected_return_low",
            "horizon_days",
            "macro_series",
            "mandate",
            "optimization_inputs",
            "peer_inputs",
            "performance_benchmark_exchange",
            "performance_benchmark_symbol",
            "portfolio_code",
            "portfolio_value",
            "proposed_trade",
            "risk_metrics",
            "signal_inputs",
            "sizing_inputs",
        }
    )
    symbol = serializers.CharField(max_length=32)
    exchange = serializers.CharField(max_length=32, default="US")
    scope = serializers.ChoiceField(choices=AnalysisScope.choices, default=AnalysisScope.SINGLE)
    config = serializers.DictField(required=False, default=dict)
    as_of = serializers.DateTimeField(required=False, default=timezone.now)

    def validate_symbol(self, value: str) -> str:
        return value.strip().upper()

    def validate_exchange(self, value: str) -> str:
        return value.strip().upper()

    def validate_scope(self, value: str) -> str:
        if value != AnalysisScope.SINGLE:
            raise serializers.ValidationError(
                "This endpoint creates one security analysis at a time; submit one run per security."
            )
        return value

    def validate_config(self, value: dict) -> dict:
        unknown = sorted(set(value) - self.ALLOWED_CONFIG_KEYS)
        if unknown:
            raise serializers.ValidationError(
                f"Unsupported analysis configuration keys: {', '.join(unknown)}"
            )
        if value.get("agent_inputs") and not settings.ALLOW_API_AGENT_INPUT_OVERRIDES:
            raise serializers.ValidationError(
                "Direct agent-input overrides are disabled for API requests."
            )
        return validate_bounded_json(value, field_name="config")

    def validate_as_of(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("The analysis cutoff cannot be in the future.")
        return value


class PipelineStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStepResult
        fields = (
            "id",
            "step_name",
            "sequence",
            "status",
            "attempt",
            "warnings",
            "error_message",
            "duration_ms",
            "started_at",
            "completed_at",
        )


class AnalysisRunSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="ticker.symbol", read_only=True)
    exchange = serializers.CharField(source="ticker.exchange", read_only=True)
    initiated_by = serializers.CharField(
        source="initiated_by.username",
        allow_null=True,
        read_only=True,
    )
    steps = PipelineStepSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisRun
        fields = (
            "id",
            "symbol",
            "exchange",
            "scope",
            "status",
            "current_stage",
            "initiated_by",
            "celery_task_id",
            "data_cutoff_at",
            "configuration_hash",
            "manifest_hash",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
            "steps",
        )


class SpecialistReportSerializer(serializers.ModelSerializer):
    specialist = serializers.CharField(source="specialist_type", read_only=True)

    class Meta:
        model = SpecialistReport
        fields = (
            "id",
            "specialist",
            "thesis",
            "summary",
            "evidence",
            "assumptions",
            "limitations",
            "confidence",
            "stance",
            "generated_at",
            "agent_version",
            "model_version",
            "prompt_version",
            "version",
        )


class BullBearDecisionMemoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BullBearDecisionMemo
        exclude = ("run", "ticker", "analysis_run_id")


class ConvictionScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConvictionScorePackage
        exclude = ("run", "ticker", "analysis_run_id")


class SignalAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignalAgreementMatrix
        exclude = ("run", "ticker", "analysis_run_id")


class ConvictionResponseSerializer(serializers.Serializer):
    score = ConvictionScoreSerializer()
    agreement = SignalAgreementSerializer()


class RiskValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskValidationResult
        exclude = ("analysis_run",)


class ComplianceResultSerializer(serializers.ModelSerializer):
    reviewer = serializers.CharField(source="reviewer.username", allow_null=True, read_only=True)

    class Meta:
        model = ComplianceResult
        exclude = ("analysis_run",)


class RiskComplianceResponseSerializer(serializers.Serializer):
    risk = RiskValidationSerializer()
    compliance = ComplianceResultSerializer()
    approval_gate = serializers.DictField()


class PMRecommendationSerializer(serializers.ModelSerializer):
    reviewer = serializers.CharField(source="reviewer.username", allow_null=True, read_only=True)
    review_request = serializers.SerializerMethodField()

    @staticmethod
    def get_review_request(obj) -> dict | None:
        if not hasattr(obj, "review_request"):
            return None
        review = obj.review_request
        return {
            "id": str(review.id),
            "status": review.status,
            "expires_at": review.expires_at,
            "version": review.lock_version,
            "decision": review.decision or None,
            "decided_at": review.decided_at,
        }

    class Meta:
        model = PMRecommendation
        exclude = ("analysis_run", "ticker")


class PMReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=("approve", "reject", "defer"))
    rationale = serializers.CharField(max_length=4000, trim_whitespace=True)
    expected_version = serializers.IntegerField(min_value=1)

    def validate_rationale(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("A review rationale is required.")
        return value.strip()
