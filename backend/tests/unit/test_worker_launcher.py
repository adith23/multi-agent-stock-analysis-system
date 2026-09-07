from __future__ import annotations

import pytest

from config.worker import build_worker_argv, default_pool


def test_windows_worker_uses_concurrent_thread_pool() -> None:
    argv = build_worker_argv([], platform_name="nt", environ={})

    assert "--pool=threads" in argv
    assert "--concurrency=4" in argv
    assert "--pool=solo" not in argv


def test_posix_worker_uses_concurrent_prefork_pool() -> None:
    argv = build_worker_argv([], platform_name="posix", environ={})

    assert default_pool("posix") == "prefork"
    assert "--pool=prefork" in argv
    assert "--concurrency=4" in argv


def test_worker_options_can_be_overridden() -> None:
    argv = build_worker_argv(
        ["--without-gossip"],
        platform_name="nt",
        environ={
            "CELERY_WORKER_POOL": "threads",
            "CELERY_WORKER_CONCURRENCY": "8",
            "CELERY_WORKER_QUEUES": "ingestion,orchestrator",
        },
    )

    assert "--concurrency=8" in argv
    assert "--queues=ingestion,orchestrator" in argv
    assert argv[-1] == "--without-gossip"


def test_worker_rejects_non_positive_concurrency() -> None:
    with pytest.raises(SystemExit):
        build_worker_argv(["--concurrency=0"], platform_name="nt", environ={})
