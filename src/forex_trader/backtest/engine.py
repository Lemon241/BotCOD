from dataclasses import asdict
from datetime import timedelta
from uuid import uuid4

import pandas as pd

from forex_trader.backtest.metrics import financial_metrics
from forex_trader.domain.models import Trade
from forex_trader.labels.barrier import Outcome, barrier_event
from forex_trader.risk.manager import AccountState, RiskManager


class BacktestEngine:
    def __init__(self, config):
        self.c = config

    def run(self, m1: pd.DataFrame, signals: list[dict]):
        risk = self.c.section("risk")
        costs = self.c.section("costs")
        barriers = self.c.section("barriers")
        bt = self.c.section("backtest")
        balance = risk["initial_equity"]
        state = AccountState(balance, balance, balance, m1.index[0].date(), balance)
        risk_manager = RiskManager(
            risk["risk_per_trade_pct"],
            risk["max_open_positions"],
            risk["max_daily_loss_pct"],
            risk["max_drawdown_pct"],
        )
        trades = []
        curve = []
        last_exit = None
        for signal in signals:
            if signal["action"] == "NO_TRADE":
                continue
            signal_time = pd.Timestamp(signal["timestamp"])
            if last_exit is not None and signal_time <= last_exit:
                continue
            if signal_time.date() != state.day:
                state.day = signal_time.date()
                state.day_start_equity = state.equity
            candidates = m1.loc[m1.index > signal_time].head(self.c.section("execution")["max_entry_wait_minutes"])
            if candidates.empty:
                continue
            entry_time = candidates.index[0]
            row = candidates.iloc[0]
            spread = float(row.get("spread", costs["default_spread_pips"]))
            direction = signal["action"]
            pip = self.c.pip_size
            mid = float(row.open)
            entry = mid + (spread / 2 + costs["slippage_pips"]) * pip * (1 if direction == "LONG" else -1)
            tp_pips = signal["take_profit"]
            sl_pips = signal["stop_loss"]
            approval = risk_manager.assess(state, sl_pips, pip)
            if not approval.approved:
                continue
            size = approval.units
            horizon = m1.loc[
                (m1.index >= entry_time) & (m1.index <= entry_time + timedelta(minutes=barriers["max_holding_minutes"]))
            ]
            outcome, exit_time = barrier_event(
                horizon, direction, entry, tp_pips * pip, sl_pips * pip, bt["ambiguous_policy"]
            )
            if outcome == Outcome.TP_FIRST:
                exit_price = entry + (tp_pips * pip if direction == "LONG" else -tp_pips * pip)
                result = "TP"
            elif outcome == Outcome.SL_FIRST:
                exit_price = entry - (sl_pips * pip if direction == "LONG" else -sl_pips * pip)
                result = "SL"
            else:
                exit_price = float(horizon.close.iloc[-1])
                result = outcome.value
            gross = (exit_price - entry) * (1 if direction == "LONG" else -1) * size
            transaction = (spread + 2 * costs["slippage_pips"]) * pip * size + costs["commission_per_unit"] * size
            # Costs are explicit and charged once; gross PnL excludes transaction costs.
            if outcome == Outcome.TP_FIRST:
                gross = tp_pips * pip * size
            elif outcome == Outcome.SL_FIRST:
                gross = -sl_pips * pip * size
            net = gross - transaction
            balance += net
            trade = Trade(
                str(uuid4()),
                direction,
                signal_time.to_pydatetime(),
                entry_time.to_pydatetime(),
                entry,
                entry - sl_pips * pip * (1 if direction == "LONG" else -1),
                entry + tp_pips * pip * (1 if direction == "LONG" else -1),
                size,
                spread,
                costs["slippage_pips"],
                signal["p_success"],
                signal["expected_value"],
                signal.get("m15_regime", "UNKNOWN"),
                signal.get("model_version", "baseline"),
                exit_time.to_pydatetime(),
                exit_price,
                gross,
                transaction,
                net,
                result,
            )
            trades.append(asdict(trade))
            state.equity = state.balance = balance
            state.peak_equity = max(state.peak_equity, balance)
            last_exit = exit_time
            curve.append(
                {
                    "timestamp": exit_time,
                    "balance": balance,
                    "equity": balance,
                    "drawdown": (state.peak_equity - balance) / state.peak_equity,
                    "open_position": 0,
                    "realized_pnl": net,
                    "unrealized_pnl": 0,
                }
            )
        trades_df = pd.DataFrame(trades)
        equity_df = pd.DataFrame(curve)
        return trades_df, equity_df, financial_metrics(trades_df, equity_df)
