"""Deterministic hashing helpers for provenance and deduplication."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, (date, datetime, Decimal, Enum)):
        return str(value)
    if isinstance(value, set | frozenset):
        return sorted(value, key=str)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        default=_json_default,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def content_hash(value: Any) -> str:
    """Return a stable SHA-256 hash for text or JSON-compatible data."""

    payload = value if isinstance(value, str | bytes) else canonical_json(value)
    encoded = payload if isinstance(payload, bytes) else payload.encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def simhash(value: str, *, bits: int = 64) -> int:
    """Compute a deterministic SimHash fingerprint for near-duplicate text."""

    if bits <= 0:
        raise ValueError("bits must be positive")
    vector = [0] * bits
    for token in TOKEN_PATTERN.findall(value.casefold()):
        digest = int.from_bytes(hashlib.sha256(token.encode()).digest(), "big")
        for index in range(bits):
            vector[index] += 1 if digest & (1 << index) else -1
    return sum(1 << index for index, score in enumerate(vector) if score >= 0)


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def redact_mapping(
    value: Mapping[str, Any],
    *,
    sensitive_keys: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Recursively redact common credential and token fields."""

    keys = sensitive_keys or frozenset(
        {
            "password",
            "token",
            "access_token",
            "refresh",
            "refresh_token",
            "secret",
            "api_key",
            "authorization",
        }
    )
    redacted: dict[str, Any] = {}
    for key, item in value.items():
        if key.casefold() in keys:
            redacted[key] = "[REDACTED]"
        elif isinstance(item, Mapping):
            redacted[key] = redact_mapping(item, sensitive_keys=keys)
        elif isinstance(item, list):
            redacted[key] = [
                redact_mapping(entry, sensitive_keys=keys) if isinstance(entry, Mapping) else entry
                for entry in item
            ]
        else:
            redacted[key] = item
    return redacted
