"""Typed LLM runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True, slots=True)
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_retries: int
    request_timeout_seconds: int

    @classmethod
    def from_settings(
        cls,
        *,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> LLMConfig:
        return cls(
            provider=provider or settings.LLM_PROVIDER,
            model=model or settings.LLM_DEFAULT_MODEL,
            temperature=(settings.LLM_TEMPERATURE if temperature is None else temperature),
            max_retries=settings.LLM_MAX_RETRIES,
            request_timeout_seconds=settings.LLM_REQUEST_TIMEOUT_SECONDS,
        )
