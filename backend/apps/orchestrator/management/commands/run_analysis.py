from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.market_data.models import Ticker
from apps.orchestrator.services import PipelineService


class Command(BaseCommand):
    help = "Create and dispatch one point-in-time security analysis."

    def add_arguments(self, parser) -> None:
        parser.add_argument("symbol")
        parser.add_argument("--exchange", default="US")
        parser.add_argument("--username", required=True)
        parser.add_argument("--config", default="{}", help="JSON analysis configuration.")
        parser.add_argument("--as-of", help="ISO-8601 point-in-time data cutoff.")
        parser.add_argument(
            "--no-dispatch",
            action="store_true",
            help="Create the run without publishing the Celery canvas.",
        )

    def handle(self, *args, **options) -> None:
        try:
            config = json.loads(options["config"])
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid --config JSON: {exc}") from exc
        if not isinstance(config, dict):
            raise CommandError("--config must decode to a JSON object.")
        ticker = Ticker.objects.active().for_symbol(options["symbol"], options["exchange"]).first()
        if ticker is None:
            raise CommandError("No active ticker matches symbol and exchange.")
        user = (
            get_user_model().objects.filter(username=options["username"], is_active=True).first()
        )
        if user is None:
            raise CommandError("The initiating user does not exist or is inactive.")
        cutoff = timezone.now()
        if options["as_of"]:
            cutoff = parse_datetime(options["as_of"])
            if cutoff is None:
                raise CommandError("--as-of must be a valid ISO-8601 datetime.")
            if timezone.is_naive(cutoff):
                cutoff = timezone.make_aware(cutoff, timezone.get_current_timezone())
            if cutoff > timezone.now():
                raise CommandError("--as-of cannot be in the future.")

        service = PipelineService()
        run = service.create_run(
            ticker=ticker,
            initiated_by=user,
            config=config,
            data_cutoff_at=cutoff,
        )
        task_id = None if options["no_dispatch"] else service.dispatch(run)
        self.stdout.write(
            self.style.SUCCESS(
                json.dumps(
                    {
                        "analysis_run_id": str(run.id),
                        "manifest_hash": run.manifest_hash,
                        "celery_task_id": task_id,
                    }
                )
            )
        )
