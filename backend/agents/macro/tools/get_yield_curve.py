from __future__ import annotations

from langchain_core.tools import tool


@tool
def get_yield_curve(yields: dict[str, float]) -> dict[str, float | str]:
    """Compute common yield-curve spreads from normalized tenor yields."""

    required = {"3m", "2y", "10y"}
    missing = required - yields.keys()
    if missing:
        raise ValueError(f"missing yield tenors: {', '.join(sorted(missing))}")
    spread_10y_2y = float(yields["10y"]) - float(yields["2y"])
    spread_10y_3m = float(yields["10y"]) - float(yields["3m"])
    return {
        "10y_2y": round(spread_10y_2y, 6),
        "10y_3m": round(spread_10y_3m, 6),
        "shape": (
            "inverted"
            if min(spread_10y_2y, spread_10y_3m) < 0
            else ("flat" if max(abs(spread_10y_2y), abs(spread_10y_3m)) < 0.25 else "normal")
        ),
    }
