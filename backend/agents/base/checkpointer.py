"""Managed PostgresSaver lifecycle for durable LangGraph state."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from django.conf import settings

from apps.core.domain.exceptions import ConfigurationError


@contextmanager
def get_checkpointer(
    connection_string: str | None = None,
    *,
    setup: bool = False,
) -> Iterator[Any]:
    """Yield a PostgresSaver and always close its connection resources.

    ``setup=True`` is intended for deployment/bootstrap. Normal request and
    worker paths should use migrations/bootstrap once, then leave it false.
    """

    database_url = connection_string or settings.LANGGRAPH_DATABASE_URL
    if not database_url:
        raise ConfigurationError("LANGGRAPH_DATABASE_URL is required")

    from langgraph.checkpoint.postgres import PostgresSaver

    with PostgresSaver.from_conn_string(database_url) as checkpointer:
        if setup:
            checkpointer.setup()
        yield checkpointer
