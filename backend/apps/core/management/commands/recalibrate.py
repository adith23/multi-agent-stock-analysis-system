from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.portfolio.services import PerformanceService
from ml.regime import RegimeClassifier


class Command(BaseCommand):
    help = "Assess recommendation performance or fit a versioned regime model artifact."

    def add_arguments(self, parser) -> None:
        parser.add_argument("target", choices=("performance", "regime"))
        parser.add_argument("--features", help="JSON file containing a 2D feature matrix.")
        parser.add_argument("--output", help="Output model path, under ML_MODEL_DIR by default.")
        parser.add_argument("--n-regimes", type=int, default=5)
        parser.add_argument(
            "--state-labels",
            default="{}",
            help="Optional JSON mapping from learned state ID to reviewed semantic label.",
        )

    def handle(self, *args, **options) -> None:
        if options["target"] == "performance":
            self.stdout.write(json.dumps(PerformanceService.summary(), default=str))
            return
        if not options["features"]:
            raise CommandError("--features is required for regime recalibration.")
        source = Path(options["features"]).expanduser().resolve()
        if not source.is_file():
            raise CommandError("The feature file does not exist.")
        try:
            features = np.asarray(json.loads(source.read_text(encoding="utf-8")), dtype=float)
            raw_labels = json.loads(options["state_labels"])
            labels = {int(state): str(label) for state, label in raw_labels.items()}
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Invalid recalibration input: {exc}") from exc
        n_regimes = options["n_regimes"]
        if labels and set(labels) != set(range(n_regimes)):
            raise CommandError("--state-labels must define every learned state exactly once.")
        destination = (
            Path(options["output"]).expanduser()
            if options["output"]
            else Path(settings.ML_MODEL_DIR) / "regime.joblib"
        ).resolve()
        temporary = destination.with_suffix(f"{destination.suffix}.tmp")
        classifier = RegimeClassifier(n_regimes=n_regimes, regime_map=labels).fit(features)
        classifier.save(str(temporary))
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.replace(destination)
        self.stdout.write(
            self.style.SUCCESS(
                json.dumps(
                    {
                        "model": classifier.model_name,
                        "version": classifier.model_version,
                        "path": str(destination),
                        "state_labels_reviewed": bool(labels),
                    }
                )
            )
        )
