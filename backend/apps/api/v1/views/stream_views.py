from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator
from uuid import UUID

from asgiref.sync import sync_to_async
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.views import View
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.core.domain.enums import PipelineStatus
from apps.core.events import format_heartbeat, format_sse_comment, format_sse_event
from apps.core.events.bus import EventBus
from apps.orchestrator.models import AnalysisRun, PipelineStepResult

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_SECONDS = 15.0


def _authenticate_request(request) -> AccessToken | None:
    """Validate JWT from Authorization Bearer header or fallback query parameter."""
    auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION", "")
    token_str = ""

    if auth_header.startswith("Bearer "):
        token_str = auth_header[7:].strip()
    elif "token" in request.GET:
        token_str = request.GET["token"].strip()

    if not token_str:
        return None

    try:
        return AccessToken(token_str)
    except (InvalidToken, TokenError):
        return None


def _get_last_event_id(request) -> str | None:
    """Extract Last-Event-ID from standard header or fallback query parameter."""
    return (
        request.headers.get("Last-Event-ID")
        or request.META.get("HTTP_LAST_EVENT_ID")
        or request.GET.get("last_event_id")
    )


class PipelineStreamView(View):
    """ASGI-native Server-Sent Events stream for individual analysis run progress."""

    async def get(self, request, run_id: UUID) -> HttpResponse:
        token = _authenticate_request(request)
        if token is None:
            return JsonResponse({"detail": "Authentication credentials were not provided or invalid."}, status=401)

        run_id_str = str(run_id)
        last_event_id = _get_last_event_id(request)

        # Check if run exists
        run_data = await self._get_run_data(run_id_str)
        if not run_data:
            return JsonResponse({"detail": "Analysis run not found."}, status=404)

        response = StreamingHttpResponse(
            self._event_generator(run_id_str, run_data, last_event_id),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response

    @sync_to_async
    def _get_run_data(self, run_id_str: str) -> dict | None:
        run = AnalysisRun.objects.filter(id=run_id_str).first()
        if not run:
            return None
        return {
            "status": run.status,
            "current_stage": run.current_stage,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }

    @sync_to_async
    def _get_historical_steps(self, run_id_str: str) -> list[dict]:
        steps = (
            PipelineStepResult.objects.filter(analysis_run_id=run_id_str)
            .order_by("sequence", "attempt")
            .values("id", "step_name", "sequence", "status", "output_snapshot", "started_at", "completed_at")
        )
        return list(steps)

    async def _event_generator(
        self,
        run_id_str: str,
        initial_run: dict,
        last_event_id: str | None,
    ) -> AsyncGenerator[str, None]:
        # Send an immediate connection acknowledgment comment
        yield format_sse_comment("connected")

        # Replay historical steps for catch-up
        historical_steps = await self._get_historical_steps(run_id_str)
        for step in historical_steps:
            step_id = str(step["id"])
            if last_event_id and step_id <= last_event_id:
                continue

            event_type = "stage_completed" if step["status"] == "completed" else "stage_started"
            yield format_sse_event(
                event_type=event_type,
                data={
                    "stage": step["step_name"],
                    "sequence": step["sequence"],
                    "timestamp": (step["completed_at"] or step["started_at"] or timezone.now()).isoformat()
                    if hasattr(step["completed_at"] or step["started_at"], "isoformat")
                    else str(step["completed_at"] or step["started_at"]),
                    "output": step.get("output_snapshot", {}),
                },
                event_id=step_id,
            )

        # If run is already completed or failed, emit terminal event and close
        current_status = initial_run["status"]
        if current_status == PipelineStatus.COMPLETED:
            yield format_sse_event(
                "pipeline_completed",
                {
                    "run_id": run_id_str,
                    "timestamp": initial_run["completed_at"] or timezone.now().isoformat(),
                },
            )
            return

        if current_status in {PipelineStatus.FAILED, PipelineStatus.CANCELLED}:
            yield format_sse_event(
                "pipeline_failed",
                {
                    "run_id": run_id_str,
                    "stage": initial_run["current_stage"] or "failed",
                    "error": initial_run["error_message"] or "Pipeline failed",
                    "timestamp": initial_run["completed_at"] or timezone.now().isoformat(),
                },
            )
            return

        # Otherwise subscribe to Redis channel
        channel = f"pipeline:{run_id_str}"
        try:
            generator = EventBus.listen_channel(channel)
            while True:
                try:
                    event = await asyncio.wait_for(generator.__anext__(), timeout=HEARTBEAT_INTERVAL_SECONDS)
                    event_type = event.get("event", "message")
                    data = event.get("data", {})
                    event_id = event.get("id")

                    yield format_sse_event(
                        event_type=event_type,
                        data=data,
                        event_id=event_id,
                    )

                    # Terminate stream on terminal events
                    if event_type in {"pipeline_completed", "pipeline_failed"}:
                        break

                except asyncio.TimeoutError:
                    # Emit heartbeat keep-alive comment
                    yield format_heartbeat()

                    # Liveness check on DB in case event was missed
                    fresh = await self._get_run_data(run_id_str)
                    if fresh and fresh["status"] == PipelineStatus.COMPLETED:
                        yield format_sse_event(
                            "pipeline_completed",
                            {"run_id": run_id_str, "timestamp": fresh["completed_at"] or timezone.now().isoformat()},
                        )
                        break
                    elif fresh and fresh["status"] in {PipelineStatus.FAILED, PipelineStatus.CANCELLED}:
                        yield format_sse_event(
                            "pipeline_failed",
                            {
                                "run_id": run_id_str,
                                "stage": fresh["current_stage"] or "failed",
                                "error": fresh["error_message"] or "Pipeline ended",
                                "timestamp": fresh["completed_at"] or timezone.now().isoformat(),
                            },
                        )
                        break

        except (asyncio.CancelledError, GeneratorExit):
            logger.info("SSE client disconnected from pipeline stream %s", run_id_str)
        except Exception as exc:
            logger.warning("Pipeline stream error on %s: %s", run_id_str, exc)


class AlertStreamView(View):
    """ASGI-native Server-Sent Events stream for system-wide market alerts."""

    async def get(self, request) -> HttpResponse:
        token = _authenticate_request(request)
        if token is None:
            return JsonResponse({"detail": "Authentication credentials were not provided or invalid."}, status=401)

        response = StreamingHttpResponse(
            self._event_generator(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response

    async def _event_generator(self) -> AsyncGenerator[str, None]:
        yield format_sse_comment("connected")

        channel = "alerts:stream"
        try:
            generator = EventBus.listen_channel(channel)
            while True:
                try:
                    event = await asyncio.wait_for(generator.__anext__(), timeout=HEARTBEAT_INTERVAL_SECONDS)
                    event_type = event.get("event", "message")
                    data = event.get("data", {})
                    event_id = event.get("id")

                    yield format_sse_event(
                        event_type=event_type,
                        data=data,
                        event_id=event_id,
                    )
                except asyncio.TimeoutError:
                    yield format_heartbeat()
        except (asyncio.CancelledError, GeneratorExit):
            logger.info("SSE client disconnected from alerts stream")
        except Exception as exc:
            logger.warning("Alerts stream error: %s", exc)
