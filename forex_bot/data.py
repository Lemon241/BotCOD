from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close"}


def load_candles(path: Path | None, periods: int = 240) -> pd.DataFrame:
    """Load validated candles, falling back to deterministic demo data."""
    if path:
        frame = pd.read_csv(path)
    else:
        rng = np.random.default_rng(42)
        returns = rng.normal(0.000015, 0.00018, periods)
        close = 1.08 + np.cumsum(returns)
        frame = pd.DataFrame(
            {
                "timestamp": pd.date_range(
                    end=pd.Timestamp.now("UTC"), periods=periods, freq="min"
                ),
                "open": np.r_[close[0], close[:-1]],
                "high": close + 0.00015,
                "low": close - 0.00015,
                "close": close,
            }
        )

    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"CSV privo delle colonne richieste: {', '.join(sorted(missing))}")
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    frame = frame.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    numeric = ["open", "high", "low", "close"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame = frame.set_index("timestamp")
    # Time interpolation prevents a missing candle from becoming a false sharp signal.
    frame[numeric] = frame[numeric].interpolate(method="time", limit_direction="both")
    if frame[numeric].isna().any().any() or (frame[numeric] <= 0).any().any():
        raise ValueError("I prezzi devono essere numerici, positivi e interpolabili")
    return frame
