from forex_trader.backtest.metrics import maximum_drawdown


def test_maximum_drawdown():
    assert maximum_drawdown([100, 120, 90, 110]) == 0.25
