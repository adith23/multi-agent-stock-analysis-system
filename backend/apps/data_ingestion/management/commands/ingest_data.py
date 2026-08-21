from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.data_ingestion.domain import DataCategory
from apps.data_ingestion.models import DataSourceConfiguration
from apps.data_ingestion.services import IngestionService
from apps.data_ingestion.tasks import ingest_enabled_sources


class Command(BaseCommand):
    help = "Run or schedule canonical data ingestion through configured connectors."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--source", help="Configured source type for a single ingestion.")
        parser.add_argument(
            "--category",
            action="append",
            choices=DataCategory.values,
            dest="categories",
        )
        parser.add_argument("--params", default="{}", help="Connector parameters as JSON.")
        parser.add_argument("--synchronous", action="store_true")

    def handle(self, *args, **options) -> None:
        categories = options["categories"] or list(DataCategory.values)
        try:
            params = json.loads(options["params"])
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid --params JSON: {exc}") from exc
        if not isinstance(params, dict):
            raise CommandError("--params must decode to a JSON object.")

        if options["source"]:
            if len(categories) != 1:
                raise CommandError("A single --category is required with --source.")
            config = DataSourceConfiguration.objects.filter(
                source_type=options["source"],
                is_enabled=True,
            ).first()
            if config is None:
                raise CommandError("The requested source is missing or disabled.")
            category = categories[0]
            if category not in config.supported_categories:
                raise CommandError("The source does not support the requested category.")
            if options["synchronous"]:
                result = IngestionService().ingest(config, category, **params)
                payload = result.model_dump(mode="json")
            else:
                from apps.data_ingestion.tasks import ingest_source

                task = ingest_source.delay(config.source_type, category, params)
                payload = {"scheduled_task_ids": [task.id]}
        elif options["synchronous"]:
            raise CommandError("--synchronous requires --source and one --category.")
        else:
            task = ingest_enabled_sources.delay(categories)
            payload = {"scheduler_task_id": task.id}
        self.stdout.write(self.style.SUCCESS(json.dumps(payload, default=str)))
