import numpy as np

from engines.peer import RelativeValueEngine
from engines.performance import HitRateEngine, ReturnAttributionEngine, SignalDecayEngine
from engines.scenario import ScenarioEngine
from ml import ml_model_registry
from ml.attention import NewsAttentionDetector
from ml.finbert import FinBERTClassifier
from ml.regime import RegimeClassifier


def test_peer_relative_value_ranking() -> None:
    result = RelativeValueEngine().compute(
        {
            "target": "A",
            "companies": [
                {
                    "symbol": "A",
                    "pe": 10,
                    "ev_ebitda": 6,
                    "revenue_growth": 0.2,
                    "roe": 0.25,
                    "momentum": 0.15,
                },
                {
                    "symbol": "B",
                    "pe": 20,
                    "ev_ebitda": 10,
                    "revenue_growth": 0.1,
                    "roe": 0.15,
                    "momentum": 0.05,
                },
            ],
            "metrics": ["pe", "ev_ebitda", "revenue_growth", "roe", "momentum"],
        }
    )
    assert result["target_rank"] == 1
    assert result["preferred"] is True


def test_performance_attribution_and_decay() -> None:
    hit_rate = HitRateEngine().compute(
        {"returns": [0.1, -0.05, 0.03], "benchmark_returns": [0.02, 0.01, 0.01]}
    )
    attribution = ReturnAttributionEngine().compute(
        {
            "portfolio_weights": {"Tech": 0.6, "Health": 0.4},
            "benchmark_weights": {"Tech": 0.5, "Health": 0.5},
            "portfolio_returns": {"Tech": 0.12, "Health": 0.05},
            "benchmark_returns": {"Tech": 0.08, "Health": 0.04},
        }
    )
    decay = SignalDecayEngine().compute(
        {
            "horizons": [1, 5, 10, 20],
            "mean_returns": [0.10, 0.07, 0.04, 0.015],
        }
    )

    assert hit_rate["hit_rate"] == 0.66666667
    assert len(attribution["attribution"]) == 2
    assert decay["decay_rate"] > 0
    assert decay["half_life"] > 0


def test_custom_scenario_calculates_factor_and_asset_impacts() -> None:
    result = ScenarioEngine().compute(
        {
            "name": "rates_up",
            "positions": {"A": 600, "B": 400},
            "factor_exposures": {"A": {"rates": -0.5}, "B": {"rates": -0.2}},
            "factor_shocks": {"rates": 0.1},
            "asset_shocks": {"B": -0.05},
        }
    )
    assert result["portfolio_pnl"] == -58
    assert result["stressed_value"] == 942


def test_finbert_wrapper_uses_injected_pipeline() -> None:
    def fake_pipeline(texts, **kwargs):
        return [
            [
                {"label": "positive", "score": 0.8},
                {"label": "neutral", "score": 0.15},
                {"label": "negative", "score": 0.05},
            ]
            for _ in texts
        ]

    result = FinBERTClassifier(pipeline=fake_pipeline).classify(["Earnings beat"])

    assert result[0]["sentiment"] == "positive"
    assert result[0]["confidence"] == 0.8


def test_attention_detector_flags_news_burst() -> None:
    result = NewsAttentionDetector().predict(
        {"article_counts": [2] * 19 + [30], "burst_zscore_threshold": 2}
    )
    assert result["burst_detected"] is True
    assert result["crowding_risk"] is True


def test_regime_wrapper_supports_injected_fitted_components() -> None:
    class Scaler:
        mean_ = np.array([0.0])

        def transform(self, values):
            return values

    class Model:
        transmat_ = np.eye(2)

        def predict(self, values):
            return np.array([0] * (len(values) - 2) + [1, 1])

        def predict_proba(self, values):
            return np.tile([0.2, 0.8], (len(values), 1))

    classifier = RegimeClassifier(n_regimes=2, model=Model(), scaler=Scaler())
    result = classifier.predict(np.ones((10, 2)))
    transition = classifier.detect_transition(np.ones((10, 2)), lookback=2)

    assert result["regime"] == "regime_1"
    assert result["probability"] == 0.8
    assert transition["transition_detected"] is True
    assert set(ml_model_registry.available()) == {"attention", "finbert", "regime"}
