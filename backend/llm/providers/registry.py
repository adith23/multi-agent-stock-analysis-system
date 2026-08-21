"""Provider factory and convenience entry point."""

from __future__ import annotations

import threading
from typing import Any

from apps.core.domain.exceptions import RegistryError
from llm.config import LLMConfig
from llm.providers.base import ILLMProvider
from llm.providers.gemini_provider import GeminiProvider


class LLMProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ILLMProvider] = {}
        self._lock = threading.RLock()

    def register(self, provider: ILLMProvider, *, replace: bool = False) -> None:
        key = provider.provider_id.casefold()
        with self._lock:
            if key in self._providers and not replace:
                raise RegistryError(f"LLM provider '{key}' is already registered")
            self._providers[key] = provider

    def resolve(self, provider_id: str) -> ILLMProvider:
        key = provider_id.casefold()
        with self._lock:
            provider = self._providers.get(key)
        if provider is None:
            raise RegistryError(f"unknown LLM provider '{provider_id}'")
        return provider

    def create(self, config: LLMConfig) -> Any:
        return self.resolve(config.provider).create(config)

    def available(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._providers))


provider_registry = LLMProviderRegistry()
provider_registry.register(GeminiProvider())


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
    *,
    provider: str | None = None,
) -> Any:
    """Create the configured LangChain chat model."""

    config = LLMConfig.from_settings(
        provider=provider,
        model=model,
        temperature=temperature,
    )
    return provider_registry.create(config)
