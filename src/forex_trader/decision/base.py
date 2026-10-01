from abc import ABC, abstractmethod

from forex_trader.domain.models import Decision, MarketContext, Prediction


class DecisionEngine(ABC):
    @abstractmethod
    def decide(self, prediction: Prediction, context: MarketContext, spread_pips: float) -> Decision: ...
