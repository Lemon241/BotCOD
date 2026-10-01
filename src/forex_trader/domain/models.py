from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Action = Literal["LONG", "SHORT", "NO_TRADE"]


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    spread: float | None = None
    volume: float | None = None


@dataclass(frozen=True)
class MarketContext:
    timestamp: datetime
    trend: str
    trend_strength: float
    volatility_regime: str
    market_regime: str


@dataclass(frozen=True)
class Prediction:
    timestamp: datetime
    p_long_success: float
    p_short_success: float
    expected_upside_atr: float | None = None
    expected_downside_atr: float | None = None


@dataclass(frozen=True)
class Decision:
    action: Action
    confidence: float
    expected_value: float
    p_success: float
    take_profit: float | None
    stop_loss: float | None
    reason: str


@dataclass(frozen=True)
class TradeSignal:
    timestamp: datetime
    action: Action
    confidence: float
    expected_value: float
    stop_loss: float | None
    take_profit: float | None


@dataclass
class Trade:
    id: str
    direction: Literal["LONG", "SHORT"]
    signal_time: datetime
    entry_time: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float
    spread: float
    slippage: float
    p_success: float
    expected_value: float
    m15_regime: str
    model_version: str
    exit_time: datetime | None = None
    exit_price: float | None = None
    gross_pnl: float | None = None
    costs: float | None = None
    net_pnl: float | None = None
    result: str | None = None
