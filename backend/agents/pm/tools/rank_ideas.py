from __future__ import annotations

from typing import Any

import numpy as np
from langchain_core.tools import tool


@tool
def rank_ideas(
    ideas: list[dict[str, Any]],
    criteria: list[str],
    weights: list[float],
    beneficial: list[bool],
) -> list[dict[str, Any]]:
    """Rank candidate ideas with deterministic TOPSIS multi-criteria analysis."""

    if (
        not ideas
        or not criteria
        or len(criteria) != len(weights)
        or len(criteria) != len(beneficial)
    ):
        raise ValueError("ideas, criteria, weights, and directions must align")
    matrix = np.asarray([[float(idea[key]) for key in criteria] for idea in ideas], dtype=float)
    weights_array = np.asarray(weights, dtype=float)
    if (weights_array < 0).any() or weights_array.sum() <= 0:
        raise ValueError("TOPSIS weights must be non-negative with a positive sum")
    norms = np.linalg.norm(matrix, axis=0)
    normalized = matrix / np.where(norms == 0, 1, norms)
    weighted = normalized * (weights_array / weights_array.sum())
    positive = np.array(
        [
            weighted[:, i].max() if direction else weighted[:, i].min()
            for i, direction in enumerate(beneficial)
        ]
    )
    negative = np.array(
        [
            weighted[:, i].min() if direction else weighted[:, i].max()
            for i, direction in enumerate(beneficial)
        ]
    )
    positive_distance = np.linalg.norm(weighted - positive, axis=1)
    negative_distance = np.linalg.norm(weighted - negative, axis=1)
    score = negative_distance / np.where(
        positive_distance + negative_distance == 0,
        1,
        positive_distance + negative_distance,
    )
    ranked = sorted(
        (
            {**idea, "topsis_score": round(float(value), 8)}
            for idea, value in zip(ideas, score, strict=True)
        ),
        key=lambda item: item["topsis_score"],
        reverse=True,
    )
    return [{**item, "rank": index} for index, item in enumerate(ranked, start=1)]
