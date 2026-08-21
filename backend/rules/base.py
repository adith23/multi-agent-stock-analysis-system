from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar

from apps.core.domain.interfaces import IRuleEngine


class RuleEngine(IRuleEngine, ABC):
    VERSION: ClassVar[str] = "1.0.0"

    @property
    def rule_version(self) -> str:
        return self.VERSION

    def get_rules(self) -> list[dict[str, Any]]:
        return []
