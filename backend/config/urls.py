"""Root URL configuration."""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", lambda request: redirect("api-docs", permanent=False), name="root-redirect"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    path("api/v1/", include("apps.api.v1.urls")),
]
