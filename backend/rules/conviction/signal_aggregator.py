from __future__ import annotations

from collections import Counter
from typing import Any

from apps.core.domain.enums import AgentStance
from engines.exceptions import EngineInputError
from rules.base import RuleEngine


class SignalAggregator(RuleEngine):
    """Build the FR-064 agreement matrix and weighted consensus."""

    SCORE = {
        AgentStance.BULLISH: 1.0,
        AgentStance.NEUTRAL: 0.0,
        AgentStance.BEARISH: -1.0,
    }

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        stances = context.get("stances", {})
        if not stances:
            raise EngineInputError("at least one specialist stance is required")
        normalized = {name: AgentStance(value) for name, value in stances.items()}
        weights = {name: float(context.get("weights", {}).get(name, 1.0)) for name in normalized}
        if any(weight < 0 for weight in weights.values()) or sum(weights.values()) <= 0:
            raise EngineInputError("signal weights must be non-negative with positive sum")
        weighted_score = sum(
            self.SCORE[stance] * weights[name] for name, stance in normalized.items()
        ) / sum(weights.values())
        counts = Counter(normalized.values())
        majority_count = max(counts.values())
        consensus = majority_count / len(normalized)
        majority = max(counts, key=counts.get)
        conflicts = [name for name, stance in normalized.items() if stance is not majority]
        return {
            "stances": {name: str(stance) for name, stance in normalized.items()},
            "counts": {stance.value: counts.get(stance, 0) for stance in AgentStance},
            "weighted_direction_score": round(weighted_score, 8),
            "consensus_stance": str(majority),
            "consensus_degree": round(consensus, 8),
            "aligned_count": majority_count,
            "total_count": len(normalized),
            "conflicting_agents": conflicts,
            "rule_version": self.rule_version,
        }
