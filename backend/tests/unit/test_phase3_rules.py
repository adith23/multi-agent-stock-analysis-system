from apps.core.domain.enums import ActionSignal
from rules.compliance import ComplianceRuleEvaluator, PolicyChecker, RestrictedListChecker
from rules.conviction import ConvictionRules, SignalAggregator
from rules.risk_limits import RiskLimitChecker
from rules.time_horizon import TimeHorizonClassifier


def test_signal_agreement_and_conviction_promotion() -> None:
    stances = {
        "fundamental": "bullish",
        "technical": "bullish",
        "macro": "bullish",
        "sentiment": "bullish",
        "risk": "neutral",
    }
    agreement = SignalAggregator().evaluate({"stances": stances})
    conviction = ConvictionRules().evaluate({"stances": stances, "conviction_score": 90})

    assert agreement["consensus_stance"] == "bullish"
    assert agreement["consensus_degree"] == 0.8
    assert conviction["signal"] == ActionSignal.STRONG_BUY
    assert conviction["conviction_level"] == 5


def test_conviction_cannot_promote_without_minimum_alignment() -> None:
    result = ConvictionRules().evaluate(
        {
            "stances": {
                "fundamental": "bullish",
                "technical": "neutral",
                "macro": "neutral",
            },
            "conviction_score": 95,
        }
    )
    assert result["signal"] == "hold"


def test_time_horizon_aligns_risk_and_exit_style() -> None:
    result = TimeHorizonClassifier().evaluate(
        {"primary_driver": "fundamental", "catalyst_days": 365}
    )
    assert result["horizon"] == "strategic"
    assert result["exit_style"] == "thesis_invalidation"


def test_compliance_composite_blocks_restricted_and_policy_violations() -> None:
    evaluator = ComplianceRuleEvaluator(
        restricted_checker=RestrictedListChecker({"XYZ"}),
        policy_checker=PolicyChecker(
            [
                {
                    "id": "min-market-cap",
                    "field": "market_cap",
                    "operator": "gte",
                    "value": 1_000_000,
                    "severity": "block",
                }
            ]
        ),
    )
    restricted = evaluator.evaluate({"symbol": "XYZ", "market_cap": 2_000_000})
    violated = evaluator.evaluate({"symbol": "ABC", "market_cap": 100})
    approved = evaluator.evaluate({"symbol": "ABC", "market_cap": 2_000_000})

    assert restricted["decision"] == "restricted"
    assert violated["decision"] == "violated"
    assert approved["decision"] == "approved"


def test_risk_limits_block_and_offer_mitigations() -> None:
    result = RiskLimitChecker().evaluate(
        {
            "position_weight": 0.2,
            "sector_weight": 0.2,
            "gross_leverage": 1.0,
            "portfolio_var": 0.03,
            "days_to_liquidate": 7,
        }
    )

    assert result["decision"] == "block"
    assert "reject_trade:position_weight" in result["mitigations"]
    assert "reduce_position_size:days_to_liquidate" in result["mitigations"]
