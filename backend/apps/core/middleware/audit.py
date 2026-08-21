"""HTTP audit middleware kept thin by delegating persistence to the audit app."""

from __future__ import annotations

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class AuditLoggingMiddleware:
    """Audit authenticated actions, mutations, and request failures."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith(settings.AUDIT_EXCLUDED_PATH_PREFIXES):
            return self.get_response(request)

        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            from apps.audit.services.audit_service import AuditService

            # Capture before DRF consumes the request stream. Accessing
            # ``request.body`` also caches it for downstream parsers.
            request.audit_body = AuditService.safe_request_body(request)

        try:
            response = self.get_response(request)
        except Exception as exc:
            self._record(request, status_code=500, error=exc)
            raise

        if request.method not in {"GET", "HEAD", "OPTIONS"} or response.status_code >= 400:
            self._record(request, status_code=response.status_code)
        return response

    @staticmethod
    def _record(
        request: HttpRequest,
        *,
        status_code: int,
        error: Exception | None = None,
    ) -> None:
        from apps.audit.services.audit_service import AuditService

        AuditService.record_http_request(
            request=request,
            status_code=status_code,
            error=error,
        )
