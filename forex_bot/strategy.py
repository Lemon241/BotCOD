import numpy as np
import pandas as pd

from forex_bot.models import Side, Signal


class RegressionStrategy:
    def __init__(self, lookback: int, min_slope: float, min_r2: float) -> None:
        self.lookback = lookback
        self.min_slope = min_slope
        self.min_r2 = min_r2

    def evaluate(self, candles: pd.DataFrame) -> Signal:
        if len(candles) < self.lookback:
            raise ValueError(f"Servono almeno {self.lookback} candele")
        prices = candles["close"].iloc[-self.lookback :].to_numpy(dtype=float)
        x = np.arange(self.lookback, dtype=float)
        slope, intercept = np.polyfit(x, prices, 1)
        predicted = slope * x + intercept
        residual = np.sum((prices - predicted) ** 2)
        total = np.sum((prices - prices.mean()) ** 2)
        r2 = float(max(0.0, min(1.0, 1 - residual / total))) if total else 0.0
        normalized_slope = float(slope / prices[-1])

        if r2 < self.min_r2 or abs(normalized_slope) < self.min_slope:
            side = Side.HOLD
            reason = "trend non sufficientemente forte o stabile"
        elif normalized_slope > 0:
            side = Side.BUY
            reason = "trend lineare rialzista"
        else:
            side = Side.SELL
            reason = "trend lineare ribassista"
        return Signal(
            side=side, slope=normalized_slope, r2=r2, price=float(prices[-1]), reason=reason
        )
