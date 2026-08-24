from __future__ import annotations

from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.api.permissions import CanAccessSensitiveData, HasAnyRole, IsPortfolioManager
from apps.api.v1.filters import AnalysisRunFilter
from apps.api.v1.serializers import (
    AnalysisCreateSerializer,
    AnalysisRunSerializer,
    BullBearDecisionMemoSerializer,
    ComplianceResultSerializer,
    ConvictionResponseSerializer,
    ConvictionScoreSerializer,
    PMRecommendationSerializer,
    PMReviewSerializer,
    RiskComplianceResponseSerializer,
    RiskValidationSerializer,
    SignalAgreementSerializer,
    SpecialistReportSerializer,
)
from apps.api.validators import validate_idempotency_key
from apps.core.utils.hashing import content_hash
from apps.market_data.models import Ticker
from apps.orchestrator.models import AnalysisRun
from apps.orchestrator.services import PipelineService
from apps.portfolio.exceptions import (
    ReviewConflictError,
    ReviewExpiredError,
    ReviewSubmissionError,
)
from apps.portfolio.services import PMReviewService
from apps.users.models import UserRole

ANALYSIS_ROLES = frozenset(
    {
        UserRole.INVESTMENT_ANALYST,
        UserRole.RESEARCH_ANALYST,
        UserRole.PORTFOLIO_MANAGER,
        UserRole.SYSTEM_ADMINISTRATOR,
    }
)


class PipelineDispatchError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "The analysis was created, but the task pipeline could not be dispatched."
    default_code = "pipeline_dispatch_failed"


class ReviewConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "review_conflict"


def _analysis(run_id) -> AnalysisRun:
    return get_object_or_404(
        AnalysisRun.objects.select_related("ticker", "initiated_by").prefetch_related("steps"),
        pk=run_id,
    )


@extend_schema_view(
    post=extend_schema(
        operation_id="analysis_create",
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Unique idempotency key (1-128 chars: alphanumeric, dot, underscore, colon, hyphen) to prevent duplicate runs.",
            ),
        ],
    ),
    get=extend_schema(
        operation_id="analysis_list",
    ),
)
class AnalysisListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated, HasAnyRole)
    allowed_roles = ANALYSIS_ROLES
    filterset_class = AnalysisRunFilter
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("ticker__symbol", "ticker__name", "error_message")
    ordering_fields = ("created_at", "updated_at", "started_at", "completed_at", "status")
    ordering = ("-created_at",)
    throttle_scope = "analysis"

    def get_serializer_class(self):
        return AnalysisCreateSerializer if self.request.method == "POST" else AnalysisRunSerializer

    def get_queryset(self):
        return AnalysisRun.objects.select_related("ticker", "initiated_by").prefetch_related(
            "steps"
        )

    def post(self, request: Request, *args, **kwargs) -> Response:
        return self.create(request, *args, **kwargs)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        idempotency_key = validate_idempotency_key(request.headers.get("Idempotency-Key"))
        request_hash = content_hash(
            {
                "symbol": data["symbol"],
                "exchange": data["exchange"],
                "scope": data["scope"],
                "config": data["config"],
                "as_of": request.data.get("as_of"),
            }
        )
        existing = AnalysisRun.objects.filter(
            initiated_by=request.user,
            idempotency_key=idempotency_key,
        ).first()
        if existing is not None:
            if existing.request_hash != request_hash:
                raise ReviewConflict(
                    "The idempotency key was already used with a different analysis request."
                )
            return Response(
                AnalysisRunSerializer(existing).data,
                status=status.HTTP_200_OK,
            )
        ticker = get_object_or_404(
            Ticker.objects.active(),
            symbol=data["symbol"],
            exchange=data["exchange"],
        )
        pipeline = PipelineService()
        try:
            run = pipeline.create_run(
                ticker=ticker,
                initiated_by=request.user,
                config=data["config"],
                scope=data["scope"],
                data_cutoff_at=data["as_of"],
                idempotency_key=idempotency_key,
                request_hash=request_hash,
            )
        except IntegrityError as exc:
            run = AnalysisRun.objects.get(
                initiated_by=request.user,
                idempotency_key=idempotency_key,
            )
            if run.request_hash != request_hash:
                raise ReviewConflict(
                    "The idempotency key was already used with a different analysis request."
                ) from exc
            return Response(
                AnalysisRunSerializer(run).data,
                status=status.HTTP_200_OK,
            )
        try:
            pipeline.dispatch(run)
        except Exception as exc:
            run.fail(f"Pipeline dispatch failed: {exc}")
            raise PipelineDispatchError() from exc
        return Response(AnalysisRunSerializer(run).data, status=status.HTTP_202_ACCEPTED)


class AnalysisDetailView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AnalysisRunSerializer

    @extend_schema(operation_id="analysis_retrieve")
    def get(self, request: Request, run_id) -> Response:
        return Response(self.get_serializer(_analysis(run_id)).data)


class SpecialistReportsView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SpecialistReportSerializer

    def get(self, request: Request, run_id) -> Response:
        run = _analysis(run_id)
        reports = run.specialist_reports.order_by("specialist_type", "-version")
        return Response(self.get_serializer(reports, many=True).data)


class BullBearMemoView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BullBearDecisionMemoSerializer

    def get(self, request: Request, run_id) -> Response:
        run = _analysis(run_id)
        try:
            memo = run.decision_memo
        except AnalysisRun.decision_memo.RelatedObjectDoesNotExist as exc:
            raise NotFound("The bull/bear decision memo is not available yet.") from exc
        return Response(self.get_serializer(memo).data)


class ConvictionView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ConvictionResponseSerializer

    def get(self, request: Request, run_id) -> Response:
        run = _analysis(run_id)
        try:
            score = run.conviction_score
            matrix = run.signal_agreement
        except (
            AnalysisRun.conviction_score.RelatedObjectDoesNotExist,
            AnalysisRun.signal_agreement.RelatedObjectDoesNotExist,
        ) as exc:
            raise NotFound("Conviction scoring is not available yet.") from exc
        return Response(
            {
                "score": ConvictionScoreSerializer(score).data,
                "agreement": SignalAgreementSerializer(matrix).data,
            }
        )


class RiskComplianceView(GenericAPIView):
    permission_classes = (IsAuthenticated, CanAccessSensitiveData)
    serializer_class = RiskComplianceResponseSerializer

    def get(self, request: Request, run_id) -> Response:
        run = _analysis(run_id)
        try:
            risk = run.risk_validation
            compliance = run.compliance_result
        except (
            AnalysisRun.risk_validation.RelatedObjectDoesNotExist,
            AnalysisRun.compliance_result.RelatedObjectDoesNotExist,
        ) as exc:
            raise NotFound("Risk and compliance validation is not available yet.") from exc
        return Response(
            {
                "risk": RiskValidationSerializer(risk).data,
                "compliance": ComplianceResultSerializer(compliance).data,
                "approval_gate": run.analysis_config.get("approval_gate", {}),
            }
        )


class RecommendationView(GenericAPIView):
    permission_classes = (IsAuthenticated, CanAccessSensitiveData)
    serializer_class = PMRecommendationSerializer

    def get(self, request: Request, run_id) -> Response:
        run = _analysis(run_id)
        try:
            recommendation = run.recommendation
        except AnalysisRun.recommendation.RelatedObjectDoesNotExist as exc:
            raise NotFound("The PM recommendation is not available yet.") from exc
        payload = self.get_serializer(recommendation).data
        payload["position_sizing"] = (
            {
                "methodology": run.sizing_recommendation.methodology,
                "portfolio_weight_pct": run.sizing_recommendation.portfolio_weight_pct,
                "dollar_amount": run.sizing_recommendation.dollar_amount,
                "num_shares": run.sizing_recommendation.num_shares,
                "assumptions": run.sizing_recommendation.assumptions,
            }
            if hasattr(run, "sizing_recommendation")
            else None
        )
        payload["exit_strategy"] = (
            {
                "status": run.exit_package.status,
                "stop_loss_price": run.exit_package.stop_loss_price,
                "profit_targets": run.exit_package.profit_targets,
                "thesis_invalidation_triggers": (run.exit_package.thesis_invalidation_triggers),
                "time_based_review_date": run.exit_package.time_based_review_date,
            }
            if hasattr(run, "exit_package")
            else None
        )
        return Response(payload)


class PMReviewView(GenericAPIView):
    permission_classes = (IsAuthenticated, IsPortfolioManager)
    serializer_class = PMReviewSerializer
    decision: str | None = None
    throttle_scope = "pm_review"

    @extend_schema(
        operation_id="analysis_review_create",
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Unique idempotency key for review submission.",
            ),
        ],
    )
    def post(self, request: Request, run_id) -> Response:
        run = get_object_or_404(
            AnalysisRun.objects.select_related("ticker", "recommendation"),
            pk=run_id,
        )
        try:
            recommendation = run.recommendation
        except AnalysisRun.recommendation.RelatedObjectDoesNotExist as exc:
            raise NotFound("The PM recommendation is not available yet.") from exc
        payload = request.data.copy()
        if self.decision is not None:
            payload["decision"] = self.decision
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        idempotency_key = validate_idempotency_key(request.headers.get("Idempotency-Key"))
        try:
            submission = PMReviewService().submit(
                recommendation_id=recommendation.id,
                decision=data["decision"],
                rationale=data["rationale"],
                reviewer=request.user,
                expected_version=data["expected_version"],
                idempotency_key=idempotency_key,
            )
        except (ReviewConflictError, ReviewExpiredError) as exc:
            raise ReviewConflict(str(exc)) from exc
        except ReviewSubmissionError as exc:
            raise ValidationError({"decision": str(exc)}) from exc
        return Response(
            {
                "analysis_run_id": str(run.id),
                "decision": data["decision"],
                "status": "review_replayed" if submission.replayed else "review_accepted",
                "review_version": submission.request.lock_version,
            },
            status=status.HTTP_200_OK if submission.replayed else status.HTTP_202_ACCEPTED,
        )
