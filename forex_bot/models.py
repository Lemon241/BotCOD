from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Signal(BaseModel):
    side: Side
    slope: float
    r2: float = Field(ge=0, le=1)
    price: float
    reason: str


class Position(BaseModel):
    symbol: str
    side: Side
    units: int = Field(gt=0)
    entry_price: float
    stop_loss: float
    take_profit: float
    opened_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AccountState(BaseModel):
    balance: float
    equity: float
    realized_pnl: float = 0
    position: Position | None = None
    orders: list[dict] = Field(default_factory=list)
