import numpy as np
import pandas as pd

from forex_bot.models import Side
from forex_bot.strategy import RegressionStrategy


def candles(values: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"close": values})


def test_regression_detects_uptrend() -> None:
    signal = RegressionStrategy(20, 0.00001, 0.9).evaluate(candles(np.linspace(1.0, 1.1, 20)))
    assert signal.side == Side.BUY
    assert signal.r2 > 0.99


def test_regression_holds_on_flat_prices() -> None:
    signal = RegressionStrategy(10, 0.00001, 0.1).evaluate(candles(np.ones(10)))
    assert signal.side == Side.HOLD
