from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.earnings_quality.earnings_quality_engine import EarningsQualityEngine


@tool
def check_earnings_quality(financials: dict[str, Any]) -> dict[str, Any]:
    """Compute Beneish, Altman, and accrual quality diagnostics."""

    return EarningsQualityEngine().compute(financials)
