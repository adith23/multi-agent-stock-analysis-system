"""LangChain callbacks for agent latency, status, and failure telemetry."""

from __future__ import annotations

import time
from typing import Any

import structlog
from langchain_core.callbacks import BaseCallbackHandler

logger = structlog.get_logger(__name__)


class AgentObservabilityCallback(BaseCallbackHandler):
    """Emit structured lifecycle events without logging prompt content."""

    def __init__(self, *, agent_id: str, analysis_run_id: str) -> None:
        self.agent_id = agent_id
        self.analysis_run_id = analysis_run_id
        self._started_at: dict[str, float] = {}

    def on_chain_start(
        self,
        serialized: dict[str, Any] | None,
        inputs: dict[str, Any],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        self._started_at[str(run_id)] = time.monotonic()
        logger.info(
            "agent_chain_started",
            agent_id=self.agent_id,
            analysis_run_id=self.analysis_run_id,
            run_id=str(run_id),
        )

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        started_at = self._started_at.pop(str(run_id), time.monotonic())
        logger.info(
            "agent_chain_completed",
            agent_id=self.agent_id,
            analysis_run_id=self.analysis_run_id,
            run_id=str(run_id),
            duration_ms=round((time.monotonic() - started_at) * 1_000, 2),
        )

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        started_at = self._started_at.pop(str(run_id), time.monotonic())
        logger.error(
            "agent_chain_failed",
            agent_id=self.agent_id,
            analysis_run_id=self.analysis_run_id,
            run_id=str(run_id),
            duration_ms=round((time.monotonic() - started_at) * 1_000, 2),
            error_type=type(error).__name__,
            exc_info=error,
        )
