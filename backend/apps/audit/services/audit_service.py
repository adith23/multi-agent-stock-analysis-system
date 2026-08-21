"""Single write boundary for append-only audit events."""

from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings
from django.db import DatabaseError
from django.http import HttpRequest
from django.utils.encoding import force_str

from apps.audit.models import AuditAction, AuditTrailRecord
from apps.core.utils.hashing import redact_mapping

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def record_event(
        *,
        action: str,
        event_type: str,
        actor: Any = None,
        resource_type: str = "",
        resource_id: str = "",
        summary: str = "",
        metadata: dict[str, Any] | None = None,
        previous_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        **context: Any,
    ) -> AuditTrailRecord | None:
        """Persist an event without allowing audit failure to mask the operation."""

        authenticated_actor = actor if getattr(actor, "is_authenticated", False) else None
        actor_label = (
            getattr(authenticated_actor, "get_username", lambda: "")()
            if authenticated_actor
            else ""
        )
        try:
            return AuditTrailRecord.objects.create(
                actor=authenticated_actor,
                actor_label=actor_label,
                action=action,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=str(resource_id),
                summary=summary,
                metadata=metadata or {},
                previous_values=previous_values or {},
                new_values=new_values or {},
                **context,
            )
        except DatabaseError:
            logger.exception(
                "audit_event_persistence_failed",
                extra={"event_type": event_type, "action": action},
            )
            return None

    @classmethod
    def record_http_request(
        cls,
        *,
        request: HttpRequest,
        status_code: int,
        error: Exception | None = None,
    ) -> AuditTrailRecord | None:
        metadata: dict[str, Any] = {}
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            metadata["request_body"] = (
                request.audit_body
                if hasattr(request, "audit_body")
                else cls.safe_request_body(request)
            )
        if error is not None:
            metadata["error_type"] = type(error).__name__
            metadata["error"] = force_str(error)[:1_000]

        return cls.record_event(
            action=AuditAction.ERROR if error else AuditAction.REQUEST,
            event_type="http.request",
            actor=getattr(request, "user", None),
            summary=f"{request.method} {request.path}",
            metadata=metadata,
            request_id=getattr(request, "request_id", ""),
            method=request.method,
            path=request.path[:512],
            status_code=status_code,
            ip_address=request.META.get("REMOTE_ADDR") or None,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

    @staticmethod
    def safe_request_body(request: HttpRequest) -> dict[str, Any] | str:
        try:
            body = request.body[: settings.AUDIT_BODY_MAX_BYTES]
        except Exception:
            return "[UNAVAILABLE]"
        if not body:
            return {}
        try:
            decoded = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return "[NON_JSON_BODY]"
        return redact_mapping(decoded) if isinstance(decoded, dict) else "[NON_OBJECT_JSON]"
