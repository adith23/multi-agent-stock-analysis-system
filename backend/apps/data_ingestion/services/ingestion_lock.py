from __future__ import annotations

import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import cache


class IngestionLockTimeoutError(TimeoutError):
    pass


class IngestionLock:
    """Small cache-backed lock that suppresses duplicate provider requests."""

    def __init__(self, key: str) -> None:
        self.key = f"ingestion-lock:{key}"
        self.token = uuid.uuid4().hex
        self.timeout = int(getattr(settings, "INGESTION_LOCK_TIMEOUT_SECONDS", 600))
        self.wait_timeout = float(getattr(settings, "INGESTION_LOCK_WAIT_SECONDS", 30))

    @contextmanager
    def acquire(self) -> Iterator[bool]:
        deadline = time.monotonic() + self.wait_timeout
        while not cache.add(self.key, self.token, timeout=self.timeout):
            if time.monotonic() >= deadline:
                raise IngestionLockTimeoutError(f"Timed out waiting for {self.key}")
            time.sleep(0.25)
        try:
            yield True
        finally:
            if cache.get(self.key) == self.token:
                cache.delete(self.key)
