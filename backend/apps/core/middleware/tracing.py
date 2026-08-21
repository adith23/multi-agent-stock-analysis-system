"""Request correlation and structured-log context."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
RESPONSE_ID_HEADER = "X-Request-ID"


class RequestTracingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.META.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.META[REQUEST_ID_HEADER] = request_id
        request.request_id = request_id
        response = self.get_response(request)
        response[RESPONSE_ID_HEADER] = request_id
        return response
