import numpy as np
import pandas as pd


def true_range(frame: pd.DataFrame) -> pd.Series:
    previous = frame.close.shift(1)
    return pd.concat(
        [(frame.high - frame.low), (frame.high - previous).abs(), (frame.low - previous).abs()], axis=1
    ).max(axis=1)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    change = close.diff()
    gain = change.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = -change.clip(upper=0).ewm(alpha=1 / period, adjust=False).mean()
    return 100 - 100 / (1 + gain / loss.replace(0, np.nan))


def build_features(frame: pd.DataFrame, atr_periods=(5, 14, 30)) -> pd.DataFrame:
    f = pd.DataFrame(index=frame.index)
    candle_range = frame.high - frame.low
    safe_range = candle_range.replace(0, np.nan)
    f["body"] = frame.close - frame.open
    f["range"] = candle_range
    f["upper_wick"] = frame.high - frame[["open", "close"]].max(axis=1)
    f["lower_wick"] = frame[["open", "close"]].min(axis=1) - frame.low
    f["body_ratio"] = f.body.abs().div(safe_range).fillna(0)
    f["close_position"] = (frame.close - frame.low).div(safe_range).fillna(0)
    log_close = np.log(frame.close)
    for lag in (1, 2, 3, 5, 10, 20):
        f[f"return_{lag}"] = log_close.diff(lag)
    tr = true_range(frame)
    for period in atr_periods:
        f[f"atr_{period}"] = tr.rolling(period).mean()
    f["atr_ratio"] = f["atr_5"] / f["atr_30"]
    f["rolling_std_returns"] = log_close.diff().rolling(20).std()
    f["realized_volatility"] = np.sqrt((log_close.diff() ** 2).rolling(20).sum())
    for period in (5, 10, 20, 50):
        ema = frame.close.ewm(span=period, adjust=False).mean()
        f[f"ema_{period}"] = ema
        f[f"ema_{period}_slope"] = ema.diff(3) / 3
    f["price_distance_ema20_atr"] = (frame.close - f.ema_20) / f.atr_14
    f["ema20_distance_ema50_atr"] = (f.ema_20 - f.ema_50) / f.atr_14
    f["rsi_14"] = rsi(frame.close)
    f["roc_10"] = frame.close.pct_change(10)
    high = frame.high.rolling(20).max()
    low = frame.low.rolling(20).min()
    f["distance_high_atr"] = (high - frame.close) / f.atr_14
    f["distance_low_atr"] = (frame.close - low) / f.atr_14
    f["breakout_high"] = (frame.close > high.shift(1)).astype(int)
    f["breakout_low"] = (frame.close < low.shift(1)).astype(int)
    hour = frame.index.hour + frame.index.minute / 60
    f["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    f["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    f["day_of_week"] = frame.index.dayofweek
    return f.replace([np.inf, -np.inf], np.nan)


def market_context(frame: pd.DataFrame):
    from forex_trader.domain.models import MarketContext

    f = build_features(frame)
    row = f.iloc[-1]
    strength = min(1.0, abs(row.ema_20 - row.ema_50) / (row.atr_14 or 1))
    trend = "BULLISH" if row.ema_20 > row.ema_50 else "BEARISH"
    ratio = row.atr_ratio
    vol = "HIGH" if ratio > 1.3 else "LOW" if ratio < 0.7 else "NORMAL"
    regime = "TRENDING" if strength > 0.5 else "RANGE"
    return MarketContext(frame.index[-1].to_pydatetime(), trend, float(strength), vol, regime)
