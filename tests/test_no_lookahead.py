import pandas as pd

from forex_trader.data.pipeline import resample_ohlc, synchronize_closed


def test_m5_uses_only_closed_m15():
    idx = pd.date_range("2024-01-01 10:00", periods=30, freq="min", tz="UTC")
    raw = pd.DataFrame({"open": range(30), "high": range(30), "low": range(30), "close": range(30)}, index=idx)
    m5 = resample_ohlc(raw, "5min")
    m15 = resample_ohlc(raw, "15min")
    aligned = synchronize_closed(m5, m15)
    assert aligned.loc[pd.Timestamp("2024-01-01 10:25", tz="UTC"), "m15_close"] == 14


def test_feature_prefix_is_causal():
    from forex_trader.features.pipeline import build_features

    idx = pd.date_range("2024-01-01", periods=60, freq="min", tz="UTC")
    base = pd.DataFrame({"open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0}, index=idx)
    first = build_features(base).iloc[:40]
    base.iloc[45:] = 2
    second = build_features(base).iloc[:40]
    pd.testing.assert_frame_equal(first, second)
