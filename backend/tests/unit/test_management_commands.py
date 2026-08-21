from __future__ import annotations

import json
from contextlib import contextmanager
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.market_data.models import Ticker
from apps.orchestrator.models import AnalysisRun
from apps.users.models import User


def test_bootstrap_command_runs_migrations_and_checkpoint_setup() -> None:
    events: list[str] = []

    @contextmanager
    def fake_checkpointer(*, setup: bool):
        assert setup is True
        events.append("checkpoint")
        yield object()

    with (
        patch("apps.core.management.commands.bootstrap_infrastructure.call_command") as migrate,
        patch(
            "apps.core.management.commands.bootstrap_infrastructure.get_checkpointer",
            side_effect=fake_checkpointer,
        ),
    ):
        call_command("bootstrap_infrastructure", verbosity=0)

    migrate.assert_called_once_with("migrate", interactive=False, verbosity=0)
    assert events == ["checkpoint"]


@pytest.mark.django_db
def test_run_analysis_command_creates_manifest_without_dispatch(user: User) -> None:
    Ticker.objects.create(symbol="CMD", exchange="US", name="Command Corp")
    output = StringIO()

    call_command(
        "run_analysis",
        "CMD",
        username=user.username,
        no_dispatch=True,
        stdout=output,
    )

    payload = json.loads(output.getvalue())
    run = AnalysisRun.objects.get(pk=payload["analysis_run_id"])
    assert payload["celery_task_id"] is None
    assert payload["manifest_hash"] == run.manifest_hash


@pytest.mark.django_db
def test_ingest_data_command_schedules_enabled_sources() -> None:
    output = StringIO()
    with patch(
        "apps.data_ingestion.management.commands.ingest_data.ingest_enabled_sources.delay"
    ) as delay:
        delay.return_value.id = "ingestion-task-1"
        call_command("ingest_data", stdout=output)

    assert json.loads(output.getvalue()) == {"scheduler_task_id": "ingestion-task-1"}


@pytest.mark.django_db
def test_recalibrate_performance_command_emits_machine_readable_summary() -> None:
    output = StringIO()

    call_command("recalibrate", "performance", stdout=output)

    assert json.loads(output.getvalue())["observations"] == 0
