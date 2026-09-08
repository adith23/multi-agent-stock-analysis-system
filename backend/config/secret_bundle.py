"""Load the Always Free Secret Manager JSON bundle into process settings."""

from __future__ import annotations

import json
import os
from typing import Final

ALLOWED_SECRET_KEYS: Final = frozenset(
    {
        "ALPHA_VANTAGE_API_KEY",
        "DATABASE_URL",
        "DJANGO_SECRET_KEY",
        "FINNHUB_API_KEY",
        "FRED_API_KEY",
        "GOOGLE_API_KEY",
        "LANGGRAPH_DATABASE_URL",
        "NEWS_API_KEY",
        "REDIS_URL",
        "TAVILY_API_KEY",
    }
)


class SecretBundleError(RuntimeError):
    """Raised when the deployed secret bundle is malformed or unsafe."""


def load_secret_bundle(raw_bundle: str | None = None) -> None:
    """Populate missing environment variables from ``APP_SECRETS_JSON``.

    Explicit environment variables take precedence, which keeps local `.env`
    files and emergency per-variable overrides backward compatible.
    """
    raw_bundle = raw_bundle if raw_bundle is not None else os.environ.get("APP_SECRETS_JSON")
    if not raw_bundle:
        return
    try:
        payload = json.loads(raw_bundle)
    except json.JSONDecodeError as exc:
        raise SecretBundleError("APP_SECRETS_JSON must contain valid JSON") from exc
    if not isinstance(payload, dict):
        raise SecretBundleError("APP_SECRETS_JSON must contain a JSON object")

    unknown_keys = set(payload) - ALLOWED_SECRET_KEYS
    if unknown_keys:
        raise SecretBundleError(
            "APP_SECRETS_JSON contains unsupported keys: " + ", ".join(sorted(unknown_keys))
        )
    for key, value in payload.items():
        if not isinstance(value, str):
            raise SecretBundleError(f"Secret value {key} must be a string")
        os.environ.setdefault(key, value)
