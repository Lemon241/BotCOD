import math

import numpy as np
import pandas as pd


def maximum_drawdown(equity):
    values = np.asarray(equity, dtype=float)
    peaks = np.maximum.accumulate(values)
    return float(np.max((peaks - values) / peaks)) if len(values) else 0.0


def financial_metrics(trades: pd.DataFrame, equity: pd.DataFrame) -> dict:
    pnl = trades.net_pnl if len(trades) else pd.Series(dtype=float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(losses.sum())
    returns = equity.equity.pct_change().dropna() if len(equity) else pd.Series(dtype=float)
    downside = returns[returns < 0].std()
    std = returns.std()
    exposure = float(equity.open_position.mean()) if len(equity) else 0
    return {
        "net_profit": float(pnl.sum()),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "win_rate": float((pnl > 0).mean()) if len(pnl) else 0,
        "average_win": float(wins.mean()) if len(wins) else 0,
        "average_loss": float(losses.mean()) if len(losses) else 0,
        "profit_factor": gross_profit / abs(gross_loss) if gross_loss else None,
        "expectancy": float(pnl.mean()) if len(pnl) else 0,
        "maximum_drawdown": maximum_drawdown(equity.equity) if len(equity) else 0,
        "sharpe": float(math.sqrt(252) * returns.mean() / std) if std and not np.isnan(std) else 0,
        "sortino": float(math.sqrt(252) * returns.mean() / downside) if downside and not np.isnan(downside) else 0,
        "trade_count": len(pnl),
        "exposure": exposure,
    }
