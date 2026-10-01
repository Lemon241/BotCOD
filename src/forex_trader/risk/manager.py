from dataclasses import dataclass
from datetime import date


@dataclass
class AccountState:
    balance: float
    equity: float
    peak_equity: float
    day: date
    day_start_equity: float
    open_positions: int = 0


@dataclass(frozen=True)
class RiskApproval:
    approved: bool
    units: int
    reason: str


class RiskManager:
    def __init__(self, risk_pct: float, max_positions: int, max_daily_loss_pct: float, max_drawdown_pct: float):
        self.risk_fraction = risk_pct / 100
        self.max_positions = max_positions
        self.daily = max_daily_loss_pct / 100
        self.drawdown = max_drawdown_pct / 100

    def assess(
        self, state: AccountState, stop_pips: float, pip_value_per_unit: float, data_healthy: bool = True
    ) -> RiskApproval:
        if not data_healthy:
            return RiskApproval(False, 0, "TRADING_DISABLED: unhealthy market data")
        if state.open_positions >= self.max_positions:
            return RiskApproval(False, 0, "maximum open positions")
        if (state.day_start_equity - state.equity) / state.day_start_equity >= self.daily:
            return RiskApproval(False, 0, "TRADING_DISABLED: daily loss circuit breaker")
        if (state.peak_equity - state.equity) / state.peak_equity >= self.drawdown:
            return RiskApproval(False, 0, "TRADING_DISABLED: drawdown circuit breaker")
        units = int(state.equity * self.risk_fraction / (stop_pips * pip_value_per_unit))
        return RiskApproval(units > 0, units, "approved" if units > 0 else "position rounds to zero")
