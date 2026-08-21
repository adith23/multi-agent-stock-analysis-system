import numpy as np

from engines.exit_strategy import ProfitTargetEngine, StopLossEngine, TrailingStopEngine
from engines.portfolio_optimization import (
    HierarchicalRiskParityOptimizer,
    MeanVarianceOptimizer,
    RebalanceEngine,
    RiskParityOptimizer,
)
from engines.position_sizing import (
    FixedFractionalSizer,
    KellySizer,
    RiskParitySizer,
    VolatilityTargetSizer,
)
from engines.risk import (
    ConcentrationEngine,
    LiquidityEngine,
    StressTestEngine,
    ValueAtRiskEngine,
)


def test_var_is_seeded_and_supports_three_methods() -> None:
    rng = np.random.default_rng(7)
    returns = rng.normal(0.0005, 0.01, size=(300, 2))
    result = ValueAtRiskEngine().compute(
        {
            "returns": returns,
            "weights": [0.6, 0.4],
            "portfolio_value": 1_000_000,
            "random_seed": 12,
        }
    )

    level = result["confidence_results"]["0.95"]
    assert level["parametric_var_pct"] > 0
    assert level["historical_var_pct"] > 0
    assert level["monte_carlo_var_pct"] > 0
    assert level["historical_cvar_pct"] >= level["historical_var_pct"]


def test_stress_concentration_and_liquidity_engines() -> None:
    stress = StressTestEngine().compute(
        {
            "positions": {"A": 600_000, "B": 400_000},
            "scenarios": [{"name": "crash", "market_shock": -0.2}],
            "maximum_loss_pct": 0.1,
        }
    )
    concentration = ConcentrationEngine().compute(
        {
            "weights": {"A": 0.6, "B": 0.4},
            "sectors": {"A": "Tech", "B": "Tech"},
        }
    )
    liquidity = LiquidityEngine().compute(
        {
            "position_value": 1_000_000,
            "average_daily_value": 2_000_000,
            "bid_ask_spread_pct": 0.001,
            "volatility": 0.02,
        }
    )

    assert stress["worst_loss"] == -200_000
    assert stress["scenarios"][0]["breaches_loss_limit"] is True
    assert "sector_concentration" in concentration["alerts"]
    assert liquidity["days_to_liquidate"] == 5


def test_all_position_sizing_strategies_return_bounded_value_objects() -> None:
    strategies = [
        KellySizer(win_probability=0.6, payoff_ratio=2),
        VolatilityTargetSizer(target_volatility=0.1),
        RiskParitySizer(),
        FixedFractionalSizer(fraction=0.03),
    ]
    for strategy in strategies:
        result = strategy.calculate_size(
            conviction=75,
            volatility=0.25,
            liquidity=0.9,
            correlation=0.3,
            risk_budget=0.2,
            portfolio_value=1_000_000,
            price=100,
            maximum_weight=0.10,
            entry_tranches=2,
        )
        assert 0 <= float(result.portfolio_weight_pct) <= 10
        assert result.num_shares >= 0
        assert result.methodology == strategy.methodology_name


def test_exit_strategy_engines() -> None:
    stop = StopLossEngine().compute({"entry_price": 100, "atr": 3, "stop_loss_pct": 0.1})
    targets = ProfitTargetEngine().compute(
        {"entry_price": 100, "stop_price": stop["recommended_stop"]}
    )
    trailing = TrailingStopEngine().compute(
        {"highest_price": 120, "current_price": 109, "trailing_stop_pct": 0.1}
    )

    assert stop["recommended_stop"] < 100
    assert targets["targets"][1]["r_multiple"] == 2
    assert trailing["triggered"] is False
    assert trailing["approaching"] is True


def test_portfolio_optimization_strategies_and_rebalancing() -> None:
    expected = np.array([0.10, 0.08, 0.06])
    covariance = np.array([[0.04, 0.01, 0.005], [0.01, 0.03, 0.004], [0.005, 0.004, 0.02]])
    constraints = {"assets": ["A", "B", "C"], "maximum_weight": 0.6}
    for optimizer in (
        MeanVarianceOptimizer(),
        RiskParityOptimizer(),
        HierarchicalRiskParityOptimizer(),
    ):
        weights = optimizer.optimize(expected, covariance, constraints)
        assert abs(sum(weights.values()) - 1) < 1e-8
        assert max(weights.values()) <= 0.6 + 1e-8

    rebalance = RebalanceEngine().compute(
        {
            "current_weights": {"A": 0.7, "B": 0.3},
            "target_weights": {"A": 0.5, "B": 0.5},
            "portfolio_value": 1_000_000,
        }
    )
    assert rebalance["rebalance_required"] is True
    assert len(rebalance["trades"]) == 2
