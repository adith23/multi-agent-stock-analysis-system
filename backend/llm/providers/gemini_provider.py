"""Google Gemini provider via LangChain."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from apps.core.domain.exceptions import ConfigurationError
from llm.config import LLMConfig
from llm.providers.base import ILLMProvider


class GeminiProvider(ILLMProvider):
    provider_id = "gemini"

    def create(self, config: LLMConfig) -> Any:
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ConfigurationError("GOOGLE_API_KEY is required for the Gemini provider")

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=config.model,
            google_api_key=api_key,
            temperature=config.temperature,
            max_retries=config.max_retries,
            timeout=config.request_timeout_seconds,
        )
