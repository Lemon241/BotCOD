from forex_trader.decision.base import DecisionEngine
from forex_trader.domain.models import Decision, MarketContext, Prediction


class RuleBasedDecisionEngine(DecisionEngine):
    def __init__(
        self,
        min_probability: float,
        min_ev: float,
        min_ev_difference: float,
        tp_pips: float,
        sl_pips: float,
        max_spread: float,
        slippage: float,
        commission: float = 0,
        counter_trend_factor: float = 0.9,
    ):
        self.min_probability = min_probability
        self.min_ev = min_ev
        self.min_ev_difference = min_ev_difference
        self.tp = tp_pips
        self.sl = sl_pips
        self.max_spread = max_spread
        self.cost_extra = 2 * slippage + commission
        self.counter = counter_trend_factor

    def decide(self, prediction: Prediction, context: MarketContext, spread_pips: float) -> Decision:
        if not (0 <= prediction.p_long_success <= 1 and 0 <= prediction.p_short_success <= 1):
            return self._none("invalid probability")
        if spread_pips > self.max_spread:
            return self._none("spread above limit")
        pl = prediction.p_long_success * (self.counter if context.trend == "BEARISH" else 1)
        ps = prediction.p_short_success * (self.counter if context.trend == "BULLISH" else 1)
        cost = spread_pips + self.cost_extra
        lev = pl * self.tp - (1 - pl) * self.sl - cost
        sev = ps * self.tp - (1 - ps) * self.sl - cost
        valid_l = pl >= self.min_probability and lev >= self.min_ev
        valid_s = ps >= self.min_probability and sev >= self.min_ev
        if valid_l and valid_s and abs(lev - sev) < self.min_ev_difference:
            return self._none("EV difference too small")
        if not valid_l and not valid_s:
            return self._none("probability or EV below threshold")
        action, p, ev = ("LONG", pl, lev) if valid_l and (not valid_s or lev > sev) else ("SHORT", ps, sev)
        return Decision(action, p, ev, p, self.tp, self.sl, "positive expected value after costs")

    @staticmethod
    def _none(reason: str) -> Decision:
        return Decision("NO_TRADE", 0, 0, 0, None, None, reason)
