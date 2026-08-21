import pytest

from engines.earnings_quality import EarningsQualityEngine
from engines.exceptions import EngineInputError
from engines.financial_health import FinancialRatioEngine
from engines.valuation import DCFEngine, DividendDiscountEngine, MultiplesValuationEngine


def test_dcf_builds_ordered_scenario_values() -> None:
    result = DCFEngine().compute(
        {
            "base_free_cash_flow": 100,
            "shares_outstanding": 50,
            "net_debt": 100,
            "wacc": 0.10,
            "terminal_growth": 0.03,
            "growth_rate": 0.06,
        }
    )

    assert result["fair_value"]["bear"] < result["fair_value"]["base"]
    assert result["fair_value"]["base"] < result["fair_value"]["bull"]
    with pytest.raises(EngineInputError):
        DCFEngine().compute(
            {
                "base_free_cash_flow": 100,
                "shares_outstanding": 50,
                "net_debt": 0,
                "wacc": 0.02,
                "terminal_growth": 0.03,
            }
        )


def test_multiples_and_dividend_discount_valuation() -> None:
    multiples = MultiplesValuationEngine().compute(
        {
            "peer_pe": [15, 20, 25],
            "peer_ev_ebitda": [8, 10, 12],
            "eps": 5,
            "ebitda": 500,
            "net_debt": 100,
            "shares_outstanding": 100,
        }
    )
    ddm = DividendDiscountEngine().compute(
        {"dividend_per_share": 2, "required_return": 0.10, "growth_rate": 0.04}
    )

    assert multiples["pe_fair_value"] == 100
    assert multiples["ev_ebitda_fair_value"] == 49
    assert ddm["fair_value"] == 34.66666667


def test_financial_health_ratio_dashboard() -> None:
    result = FinancialRatioEngine().compute(
        {
            "revenue": 1000,
            "gross_profit": 500,
            "operating_income": 200,
            "net_income": 120,
            "cash_from_operations": 150,
            "current_assets": 400,
            "current_liabilities": 200,
            "total_assets": 1500,
            "total_equity": 900,
            "total_debt": 300,
            "inventory": 100,
            "interest_expense": 20,
            "previous_revenue": 900,
            "previous_net_income": 100,
        }
    )

    assert result["ratios"]["current_ratio"] == 2
    assert result["ratios"]["cash_conversion"] == 1.25
    assert 0 <= result["health_score"] <= 100


def earnings_quality_input() -> dict:
    return {
        "receivables_t": 120,
        "revenue_t": 1000,
        "receivables_t1": 100,
        "revenue_t1": 900,
        "cogs_t": 600,
        "cogs_t1": 550,
        "current_assets_t": 500,
        "current_assets_t1": 460,
        "ppe_t": 700,
        "ppe_t1": 650,
        "total_assets_t": 1800,
        "total_assets_t1": 1650,
        "depreciation_t": 70,
        "depreciation_t1": 65,
        "sga_t": 150,
        "sga_t1": 140,
        "long_term_debt_t": 300,
        "long_term_debt_t1": 320,
        "current_liabilities_t": 250,
        "current_liabilities_t1": 240,
        "net_income_t": 120,
        "cfo_t": 150,
        "retained_earnings_t": 500,
        "ebit_t": 200,
        "market_cap_t": 3000,
        "total_liabilities_t": 700,
    }


def test_earnings_quality_returns_beneish_altman_and_accruals() -> None:
    result = EarningsQualityEngine().compute(earnings_quality_input())

    assert set(result["beneish"]["components"]) == {
        "dsri",
        "gmi",
        "aqi",
        "sgi",
        "depi",
        "sgai",
        "lvgi",
        "tata",
    }
    assert result["altman"]["zone"] in {"safe", "grey", "distress"}
    assert result["high_accruals"] is False
