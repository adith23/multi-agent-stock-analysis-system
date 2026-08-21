"""Provider abstraction used by all agent graphs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from llm.config import LLMConfig


class ILLMProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @abstractmethod
    def create(self, config: LLMConfig) -> Any:
        """Create a LangChain-compatible chat model."""
