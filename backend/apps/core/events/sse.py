from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


class SSEJSONEncoder(json.JSONEncoder):
    """JSON encoder handling UUID, datetime, Decimal, and Enum instances."""

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


def format_sse_event(
    event_type: str,
    data: Any,
    event_id: str | None = None,
    retry: int | None = None,
) -> str:
    """Format an SSE message per the W3C Server-Sent Events standard.

    Wires:
      id: <event_id>
      event: <event_type>
      retry: <retry_ms>
      data: <json_string>
    """
    lines: list[str] = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    if event_type:
        lines.append(f"event: {event_type}")
    if retry is not None:
        lines.append(f"retry: {retry}")

    if isinstance(data, (dict, list)):
        payload = json.dumps(data, cls=SSEJSONEncoder)
    elif isinstance(data, str):
        payload = data
    else:
        payload = json.dumps(data, cls=SSEJSONEncoder)

    for line in payload.splitlines():
        lines.append(f"data: {line}")

    return "\n".join(lines) + "\n\n"


def format_sse_comment(comment: str = "heartbeat") -> str:
    """Format an SSE comment line.

    Per the SSE specification, lines beginning with a colon (:) are treated as comments
    and ignored by EventSource clients. Sending a comment periodically (heartbeat)
    keeps TCP sockets, reverse proxies (NGINX, Cloudflare, AWS ALB), and stateful NAT
    firewalls from closing long-lived connections.
    """
    return f": {comment}\n\n"


def format_heartbeat() -> str:
    """Format a standard SSE heartbeat comment line."""
    return format_sse_comment("heartbeat")
