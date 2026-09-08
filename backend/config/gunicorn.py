"""Gunicorn configuration shared by backend and task-worker Cloud Run services."""

from __future__ import annotations

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT_SECONDS", "300"))
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
capture_output = True
