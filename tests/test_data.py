import pandas as pd

from forex_bot.data import load_candles


def test_missing_price_is_interpolated(tmp_path) -> None:
    path = tmp_path / "prices.csv"
    pd.DataFrame(
        {
            "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z", "2026-01-01T00:02:00Z"],
            "open": [1.0, None, 1.2],
            "high": [1.1, None, 1.3],
            "low": [0.9, None, 1.1],
            "close": [1.0, None, 1.2],
        }
    ).to_csv(path, index=False)
    result = load_candles(path)
    assert result.iloc[1]["close"] == 1.1
