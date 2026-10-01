from pathlib import Path

import pandas as pd

CORE = ["open", "high", "low", "close"]


def load_market_data(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "timestamp" not in frame or not set(CORE).issubset(frame.columns):
        raise ValueError("Data requires timestamp, open, high, low, close")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    frame = frame.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    frame = frame.set_index("timestamp")
    for column in CORE + [c for c in ("spread", "tick_volume") if c in frame]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    validate_ohlc(frame)
    return frame


def validate_ohlc(frame: pd.DataFrame) -> None:
    if frame.index.tz is None or str(frame.index.tz) != "UTC":
        raise ValueError("Timestamps must be UTC")
    if frame[CORE].isna().any().any() or (frame[CORE] <= 0).any().any():
        raise ValueError("OHLC values must be finite and positive")
    invalid = (frame.high < frame[["open", "close", "low"]].max(axis=1)) | (
        frame.low > frame[["open", "close", "high"]].min(axis=1)
    )
    if invalid.any():
        raise ValueError("Invalid OHLC geometry")


def resample_ohlc(frame: pd.DataFrame, rule: str) -> pd.DataFrame:
    aggregation = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "spread" in frame:
        aggregation["spread"] = "last"
    if "tick_volume" in frame:
        aggregation["tick_volume"] = "sum"
    return frame.resample(rule, label="right", closed="left").agg(aggregation).dropna(subset=CORE)


def build_timeframes(m1: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {"m1": m1, "m5": resample_ohlc(m1, "5min"), "m15": resample_ohlc(m1, "15min")}


def synchronize_closed(signal: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    """Backward as-of join: a signal can only see a context candle already closed."""
    left = signal.sort_index().reset_index()
    right = context.sort_index().add_prefix("m15_").reset_index()
    return pd.merge_asof(left, right, on="timestamp", direction="backward").set_index("timestamp")


def temporal_split(frame: pd.DataFrame, train_fraction: float, validation_fraction: float):
    if train_fraction <= 0 or validation_fraction <= 0 or train_fraction + validation_fraction >= 1:
        raise ValueError("Temporal split fractions are invalid")
    n = len(frame)
    train_end = int(n * train_fraction)
    val_end = int(n * (train_fraction + validation_fraction))
    return frame.iloc[:train_end], frame.iloc[train_end:val_end], frame.iloc[val_end:]
