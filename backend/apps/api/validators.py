from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from django.conf import settings
from rest_framework import serializers

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

SENSITIVE_KEY_FRAGMENTS = frozenset(
    {
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "password",
        "passwd",
        "secret",
        "credential",
        "private_key",
    }
)


def validate_bounded_json(value: Any, *, field_name: str = "payload") -> Any:
    """Reject oversized, deeply nested, or credential-bearing JSON."""

    encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=True)
    maximum = int(getattr(settings, "API_MAX_JSON_BYTES", 65_536))
    if len(encoded.encode("utf-8")) > maximum:
        raise serializers.ValidationError(f"{field_name} exceeds {maximum} bytes.")
    _validate_node(value, field_name=field_name, depth=0)
    return value


def validate_idempotency_key(value: str | None) -> str:
    """Accept a log-safe, transport-safe client request identity."""

    normalized = (value or "").strip()
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(normalized):
        raise serializers.ValidationError(
            {
                "Idempotency-Key": (
                    "Use 1-128 letters, numbers, dots, underscores, colons, or hyphens."
                )
            }
        )
    return normalized


def _validate_node(value: Any, *, field_name: str, depth: int) -> None:
    maximum_depth = int(getattr(settings, "API_MAX_JSON_DEPTH", 8))
    if depth > maximum_depth:
        raise serializers.ValidationError(
            f"{field_name} exceeds the maximum nesting depth of {maximum_depth}."
        )
    if isinstance(value, Mapping):
        if len(value) > 250:
            raise serializers.ValidationError(f"{field_name} contains too many keys.")
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.casefold().replace("-", "_")
            if len(key) > 128:
                raise serializers.ValidationError(f"{field_name} contains an oversized key.")
            if any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS):
                raise serializers.ValidationError(
                    f"{field_name} must not contain credentials or secrets."
                )
            _validate_node(child, field_name=field_name, depth=depth + 1)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > 2_000:
            raise serializers.ValidationError(f"{field_name} contains too many items.")
        for child in value:
            _validate_node(child, field_name=field_name, depth=depth + 1)
