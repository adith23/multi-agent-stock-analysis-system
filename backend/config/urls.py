"""
Root URL configuration.

Reference: SYSTEM_ARCHITECTURE_AND_DESIGN.md §8.2
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # JWT Authentication
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # App API routes (uncomment as apps are implemented)
    # path("api/v1/", include("apps.core.urls")),
    # path("api/v1/analysis/", include("apps.pipeline.urls")),
    # path("api/v1/reports/", include("apps.agents.urls")),
    # path("api/v1/portfolio/", include("apps.portfolio.urls")),
    # path("api/v1/risk/", include("apps.risk.urls")),
    # path("api/v1/review/", include("apps.review.urls")),
    # path("api/v1/audit/", include("apps.audit.urls")),
    # path("api/v1/admin/", include("apps.ingestion.urls")),
]
