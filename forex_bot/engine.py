from threading import Lock

from forex_bot.broker import PaperBroker
from forex_bot.config import Settings
from forex_bot.data import load_candles
from forex_bot.models import Side
from forex_bot.risk import position_size
from forex_bot.strategy import RegressionStrategy


class TradingEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.strategy = RegressionStrategy(settings.lookback, settings.min_slope, settings.min_r2)
        self.broker = PaperBroker(
            settings.state_path,
            settings.initial_balance,
            settings.pip_size,
            settings.spread_pips,
            settings.slippage_pips,
        )
        self._lock = Lock()

    def run_cycle(self) -> dict:
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("Un ciclo e gia in esecuzione")
        try:
            candles = load_candles(self.settings.data_csv)
            signal = self.strategy.evaluate(candles)
            self.broker.mark(signal.price)
            action = "marked"
            if signal.side != Side.HOLD and not self.broker.state.position:
                units = min(
                    position_size(
                        self.broker.state.balance,
                        self.settings.risk_per_trade,
                        self.settings.stop_loss_pips,
                        self.settings.pip_size,
                    ),
                    self.settings.max_position_units,
                )
                if units:
                    self.broker.open(
                        self.settings.symbol,
                        signal.side,
                        units,
                        signal.price,
                        self.settings.stop_loss_pips,
                        self.settings.take_profit_pips,
                    )
                    action = "opened"
            return {
                "action": action,
                "signal": signal.model_dump(mode="json"),
                "state": self.broker.state.model_dump(mode="json"),
            }
        finally:
            self._lock.release()
