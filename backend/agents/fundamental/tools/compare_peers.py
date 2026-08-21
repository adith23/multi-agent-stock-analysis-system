from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.peer.relative_value_engine import RelativeValueEngine


@tool
def compare_peers(peer_inputs: dict[str, Any]) -> dict[str, Any]:
    """Rank a target company against its configured peer set."""

    return RelativeValueEngine().compute(peer_inputs)
