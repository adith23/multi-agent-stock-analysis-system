"""Celery application for outer-pipeline asynchronous execution."""

from __future__ import annotations

import os

from celery import Celery
from django_structlog.celery.steps import DjangoStructLogInitStep

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("multi_agent_stock_analysis")
app.steps["worker"].add(DjangoStructLogInitStep)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.task_routes = {
    "apps.data_ingestion.tasks.*": {"queue": "ingestion"},
    "apps.signals.tasks.*": {"queue": "computation"},
    "apps.orchestrator.tasks.run_specialist_agent": {"queue": "agents"},
    "apps.orchestrator.tasks.run_adversarial_review": {"queue": "agents"},
    "apps.orchestrator.tasks.run_risk_validation": {"queue": "agents"},
    "apps.orchestrator.tasks.run_pm_synthesis": {"queue": "agents"},
    "apps.orchestrator.tasks.resume_pm_decision": {"queue": "agents"},
    "apps.orchestrator.tasks.*": {"queue": "orchestrator"},
    "apps.portfolio.tasks.*": {"queue": "computation"},
    "apps.core.tasks.*": {"queue": "default"},
}
