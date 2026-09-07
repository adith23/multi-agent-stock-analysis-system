"""Cross-platform Celery worker launcher.

Celery's prefork pool is not supported on Windows.  Keep worker startup in one
place so local Windows workers use a real thread pool instead of silently
falling back to the single-task ``solo`` pool.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence

DEFAULT_CONCURRENCY = 4
DEFAULT_QUEUES = "default,agents,ingestion,orchestrator,computation"


def default_pool(platform_name: str | None = None) -> str:
    """Return a Celery pool supported by the current operating system."""

    return "threads" if (platform_name or os.name) == "nt" else "prefork"


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def build_worker_argv(
    argv: Sequence[str] | None = None,
    *,
    platform_name: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    """Build Celery CLI arguments, preserving additional worker options."""

    environment = os.environ if environ is None else environ
    parser = argparse.ArgumentParser(description="Start the project Celery worker")
    parser.add_argument(
        "--pool",
        default=environment.get("CELERY_WORKER_POOL", default_pool(platform_name)),
        help="Celery execution pool (defaults to threads on Windows, prefork elsewhere)",
    )
    parser.add_argument(
        "--concurrency",
        type=_positive_integer,
        default=environment.get("CELERY_WORKER_CONCURRENCY", str(DEFAULT_CONCURRENCY)),
        help=f"Concurrent worker slots (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--loglevel",
        default=environment.get("CELERY_WORKER_LOGLEVEL", "INFO"),
    )
    parser.add_argument(
        "--queues",
        default=environment.get("CELERY_WORKER_QUEUES", DEFAULT_QUEUES),
    )
    options, passthrough = parser.parse_known_args(argv)

    return [
        "celery",
        "-A",
        "config",
        "worker",
        f"--loglevel={options.loglevel}",
        f"--pool={options.pool}",
        f"--concurrency={options.concurrency}",
        f"--queues={options.queues}",
        *passthrough,
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """Launch Celery with project defaults and return its exit code."""

    from celery.bin.celery import main as celery_main

    sys.argv = build_worker_argv(argv)
    return celery_main()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
