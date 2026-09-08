"""Operational and API-discovery views."""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.api.v1.serializers import (
    APIInfoSerializer,
    LivenessSerializer,
    ReadinessSerializer,
)
from config.celery import app as celery_app


class APIRootView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = APIInfoSerializer

    def get(self, request: Request) -> Response:
        return Response(
            {
                "name": "Multi-Agent Stock Analysis API",
                "version": "v1",
                "status": "available",
            }
        )


class LivenessView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LivenessSerializer

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class ReadinessView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ReadinessSerializer

    def get(self, request: Request) -> Response:
        task_backend = str(settings.TASK_BACKEND)
        checks = {
            "database": self._database_ready(),
            "cache": self._cache_ready(),
            (
                "cloud_tasks_configuration" if task_backend == "cloud_tasks" else "celery_broker"
            ): self._task_backend_ready(),
        }
        ready = all(checks.values())
        return Response(
            {"status": "ok" if ready else "degraded", "checks": checks},
            status=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @staticmethod
    def _database_ready() -> bool:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,)
        except Exception:
            return False

    @staticmethod
    def _cache_ready() -> bool:
        key = "health:readiness"
        try:
            cache.set(key, "ok", timeout=5)
            return cache.get(key) == "ok"
        except Exception:
            return False

    @staticmethod
    def _task_backend_ready() -> bool:
        if settings.TASK_BACKEND == "cloud_tasks":
            return all(
                (
                    settings.GCP_PROJECT_ID,
                    settings.GCP_LOCATION,
                    settings.CLOUD_RUN_WORKER_URL,
                    settings.CLOUD_TASKS_SA_EMAIL,
                )
            )
        try:
            with celery_app.connection_for_read() as connection:
                connection.ensure_connection(max_retries=1, timeout=2)
            return True
        except Exception:
            return False
