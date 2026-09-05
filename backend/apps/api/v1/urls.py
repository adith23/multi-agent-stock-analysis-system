from django.urls import include, path

from .views import (
    AlertListView,
    AlertStreamView,
    AnalysisDetailView,
    AnalysisListCreateView,
    APIRootView,
    BullBearMemoView,
    CatalystListView,
    ConvictionView,
    LivenessView,
    PerformanceView,
    PipelineStreamView,
    PMReviewView,
    PortfolioRiskView,
    PortfolioStateView,
    ReadinessView,
    RecommendationView,
    RiskComplianceView,
    ScenarioCreateView,
    SpecialistReportsView,
)

app_name = "api-v1"

urlpatterns = [
    path("", APIRootView.as_view(), name="root"),
    path("health/live/", LivenessView.as_view(), name="liveness"),
    path("health/ready/", ReadinessView.as_view(), name="readiness"),
    path("auth/", include("apps.users.urls")),
    path("portfolio/", PortfolioStateView.as_view(), name="portfolio"),
    path("portfolio/risk/", PortfolioRiskView.as_view(), name="portfolio-risk"),
    path("scenarios/", ScenarioCreateView.as_view(), name="scenario-create"),
    path("performance/", PerformanceView.as_view(), name="performance"),
    path("catalysts/", CatalystListView.as_view(), name="catalyst-list"),
    path("alerts/", AlertListView.as_view(), name="alert-list"),
    path("alerts/stream/", AlertStreamView.as_view(), name="alerts-stream"),
    path("analysis/", AnalysisListCreateView.as_view(), name="analysis-list"),
    path("analysis/<uuid:run_id>/", AnalysisDetailView.as_view(), name="analysis-detail"),
    path("analysis/<uuid:run_id>/stream/", PipelineStreamView.as_view(), name="analysis-stream"),
    path(
        "analysis/<uuid:run_id>/specialists/",
        SpecialistReportsView.as_view(),
        name="analysis-specialists",
    ),
    path(
        "analysis/<uuid:run_id>/bull-bear/",
        BullBearMemoView.as_view(),
        name="analysis-bull-bear",
    ),
    path(
        "analysis/<uuid:run_id>/conviction/",
        ConvictionView.as_view(),
        name="analysis-conviction",
    ),
    path(
        "analysis/<uuid:run_id>/risk/",
        RiskComplianceView.as_view(),
        name="analysis-risk",
    ),
    path(
        "analysis/<uuid:run_id>/recommendation/",
        RecommendationView.as_view(),
        name="analysis-recommendation",
    ),
    path(
        "analysis/<uuid:run_id>/review/",
        PMReviewView.as_view(),
        name="analysis-review",
    ),
    path(
        "analysis/<uuid:run_id>/approve/",
        PMReviewView.as_view(decision="approve"),
        name="analysis-approve",
    ),
    path(
        "analysis/<uuid:run_id>/reject/",
        PMReviewView.as_view(decision="reject"),
        name="analysis-reject",
    ),
    path(
        "analysis/<uuid:run_id>/defer/",
        PMReviewView.as_view(decision="defer"),
        name="analysis-defer",
    ),
]
