import numpy as np
import pandas as pd

from forex_trader.features.pipeline import build_features, true_range


def frame(n=60):
    close = np.linspace(1, 1.1, n)
    return pd.DataFrame(
        {"open": close, "high": close + 0.01, "low": close - 0.01, "close": close},
        index=pd.date_range("2024-01-01", periods=n, freq="min", tz="UTC"),
    )


def test_flat_candle_has_zero_ratios():
    data = frame()
    data.iloc[0] = 1
    result = build_features(data)
    assert result.iloc[0].body_ratio == 0
    assert result.iloc[0].close_position == 0


def test_atr_is_true_range_average():
    data = frame()
    features = build_features(data)
    assert np.isclose(features.atr_14.iloc[-1], true_range(data).rolling(14).mean().iloc[-1])
