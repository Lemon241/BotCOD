from datetime import UTC, datetime
from pathlib import Path

from forex_bot.models import AccountState, Position, Side


class PaperBroker:
    def __init__(
        self,
        state_path: Path,
        initial_balance: float,
        pip_size: float,
        spread_pips: float,
        slippage_pips: float,
    ) -> None:
        self.path = state_path
        self.initial_balance = initial_balance
        self.pip_size = pip_size
        self.cost = (spread_pips / 2 + slippage_pips) * pip_size
        self.state = self._load()

    def _load(self) -> AccountState:
        if self.path.exists():
            return AccountState.model_validate_json(self.path.read_text())
        return AccountState(balance=self.initial_balance, equity=self.initial_balance)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(self.state.model_dump_json(indent=2))
        temporary.replace(self.path)

    def mark(self, price: float) -> None:
        pnl = 0.0
        position = self.state.position
        if position:
            direction = 1 if position.side == Side.BUY else -1
            pnl = (price - position.entry_price) * direction * position.units
            hit_stop = (
                price <= position.stop_loss if direction == 1 else price >= position.stop_loss
            )
            hit_take = (
                price >= position.take_profit if direction == 1 else price <= position.take_profit
            )
            if hit_stop or hit_take:
                self.close(price, "stop_loss" if hit_stop else "take_profit")
                return
        self.state.equity = self.state.balance + pnl
        self._save()

    def open(
        self, symbol: str, side: Side, units: int, price: float, stop_pips: float, take_pips: float
    ) -> Position:
        if side == Side.HOLD or self.state.position:
            raise ValueError("Ordine non valido o posizione gia aperta")
        direction = 1 if side == Side.BUY else -1
        entry = price + self.cost * direction
        position = Position(
            symbol=symbol,
            side=side,
            units=units,
            entry_price=entry,
            stop_loss=entry - direction * stop_pips * self.pip_size,
            take_profit=entry + direction * take_pips * self.pip_size,
        )
        self.state.position = position
        self.state.orders.append(
            {
                "event": "open",
                "at": datetime.now(UTC).isoformat(),
                **position.model_dump(mode="json"),
            }
        )
        self._save()
        return position

    def close(self, price: float, reason: str = "manual") -> float:
        position = self.state.position
        if not position:
            return 0.0
        direction = 1 if position.side == Side.BUY else -1
        exit_price = price - self.cost * direction
        pnl = (exit_price - position.entry_price) * direction * position.units
        self.state.balance += pnl
        self.state.equity = self.state.balance
        self.state.realized_pnl += pnl
        self.state.orders.append(
            {
                "event": "close",
                "at": datetime.now(UTC).isoformat(),
                "price": exit_price,
                "pnl": pnl,
                "reason": reason,
            }
        )
        self.state.position = None
        self._save()
        return pnl
