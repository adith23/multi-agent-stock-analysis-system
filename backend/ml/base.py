from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class MLModel(ABC):
    """No-download-on-import model boundary used by later agent tools."""

    MODEL_NAME: ClassVar[str]
    VERSION: ClassVar[str] = "1.0.0"

    @property
    def model_name(self) -> str:
        return self.MODEL_NAME

    @property
    def model_version(self) -> str:
        return self.VERSION

    @abstractmethod
    def predict(self, inputs: Any) -> Any: ...
