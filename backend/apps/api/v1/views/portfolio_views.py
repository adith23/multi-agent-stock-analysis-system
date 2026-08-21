from __future__ import annotations

import structlog
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.api.permissions import CanAccessSensitiveData
from apps.api.services import AlertService
from apps.api.v1.filters import CatalystFilter
from apps.api.v1.serializers import (
    AlertSerializer,
    CatalystSerializer,
    PerformanceAttributionSerializer,
    PerformanceResponseSerializer,
    PortfolioRiskSerializer,
    PortfolioStateSerializer,
    ScenarioRequestSerializer,
    ScenarioResultSerializer,
)
from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.orchestrator.models import AnalysisRun
from apps.portfolio.models import PerformanceAttributionRecord
from apps.portfolio.services import PerformanceService, ScenarioService
from apps.research.models import CatalystRecord
from apps.risk_compliance.repositories import RiskComplianceRepository

logger = structlog.get_logger(__name__)


def _latest_portfolio(request: Request):
    portfolio = RiskComplianceRepository().latest_portfolio(
        request.query_params.get("portfolio_code")
    )
    if portfolio is None:
        raise NotFound("No portfolio snapshot is available.")
    return portfolio


class PortfolioStateView(GenericAPIView):
    permission_classes = (IsAuthenticated, CanAccessSensitiveData)
    serializer_class = PortfolioStateSerializer

    def get(self, request: Request) -> Response:
        portfolio = _latest_portfolio(request)
        return Response(self.get_serializer(portfolio).data)


class PortfolioRiskView(GenericAPIView):
    permission_classes = (IsAuthenticated, CanAccessSensitiveData)
    serializer_class = PortfolioRiskSerializer

    def get(self, request: Request) -> Response:
        portfolio = _latest_portfolio(request)
        return Response(
            self.get_serializer(
                {
                    "portfolio_code": portfolio.portfolio_code,
                    "as_of": portfolio.as_of,
                    "gross_leverage": portfolio.gross_leverage,
                    "sector_exposures": portfolio.sector_exposures,
                    "factor_exposures": portfolio.factor_exposures,
                    "liquidity_metrics": portfolio.liquidity_metrics,
                    "risk_metrics": portfolio.risk_metrics,
                }
            ).data
        )


class ScenarioCreateView(GenericAPIView):
    permission_classes = (IsAuthenticated, CanAccessSensitiveData)
    serializer_class = ScenarioRequestSerializer
    throttle_scope = "scenario"

    @extend_schema(
        request=ScenarioRequestSerializer,
        responses={201: ScenarioResultSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        portfolio_code = data.pop("portfolio_code", None)
        analysis_run_id = data.pop("analysis_run_id", None)
        portfolio = (
            RiskComplianceRepository().latest_portfolio(portfolio_code) if portfolio_code else None
        )
        if portfolio_code and portfolio is None:
            raise NotFound("The requested portfolio snapshot is not available.")
        run = (
            get_object_or_404(AnalysisRun, pk=analysis_run_id)
            if analysis_run_id is not None
            else None
        )
        name = data.pop("name")
        result = ScenarioService().run(
            name=name,
            inputs=data,
            user=request.user,
            analysis_run=run,
            portfolio_state=portfolio,
        )
        AuditService.record_event(
            action=AuditAction.EXECUTE,
            event_type="portfolio.scenario_executed",
            actor=request.user,
            resource_type="ScenarioAnalysisResult",
            resource_id=str(result.id),
            summary=f"Scenario executed: {name}",
            metadata={
                "portfolio_code": portfolio_code,
                "analysis_run_id": str(analysis_run_id or ""),
            },
        )
        logger.info(
            "scenario_executed",
            scenario_id=str(result.id),
            portfolio_code=portfolio_code,
            analysis_run_id=str(analysis_run_id or ""),
        )
        return Response(
            ScenarioResultSerializer(result).data,
            status=status.HTTP_201_CREATED,
        )


class PerformanceView(GenericAPIView):
    permission_classes = (IsAuthenticated, CanAccessSensitiveData)
    serializer_class = PerformanceResponseSerializer

    def get(self, request: Request) -> Response:
        queryset = PerformanceAttributionRecord.objects.select_related(
            "recommendation__ticker"
        ).order_by("-period_end")
        if period := request.query_params.get("measurement_period"):
            queryset = queryset.filter(measurement_period=period)
        if symbol := request.query_params.get("symbol"):
            queryset = queryset.filter(recommendation__ticker__symbol__iexact=symbol)
        page = self.paginate_queryset(queryset)
        records = page if page is not None else queryset
        payload = {
            "summary": PerformanceService.summary(queryset=queryset),
            "records": PerformanceAttributionSerializer(records, many=True).data,
        }
        return self.get_paginated_response(payload) if page is not None else Response(payload)


class CatalystListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CatalystSerializer
    filterset_class = CatalystFilter
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("ticker__symbol", "title", "description", "catalyst_type")
    ordering_fields = ("expected_at", "probability", "created_at", "last_checked_at")
    ordering = ("expected_at",)

    def get_queryset(self):
        return CatalystRecord.objects.select_related("ticker").order_by("expected_at")


class AlertListView(GenericAPIView):
    permission_classes = (IsAuthenticated, CanAccessSensitiveData)
    serializer_class = AlertSerializer

    def get(self, request: Request) -> Response:
        severity = request.query_params.get("severity")
        if severity not in {None, "info", "warning", "critical"}:
            raise ValidationError({"severity": "Unknown alert severity."})
        alerts = AlertService.active(severity=severity)
        page = self.paginate_queryset(alerts)
        data = self.get_serializer(page if page is not None else alerts, many=True).data
        return self.get_paginated_response(data) if page is not None else Response(data)
