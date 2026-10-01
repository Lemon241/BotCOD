from forex_trader.decision.base import DecisionEngine


class JevDecisionEngine(DecisionEngine):
    """Extension point only. Risk rules always remain outside this adapter."""

    def decide(self, prediction, context, spread_pips):
        raise NotImplementedError("Configure an external Jev adapter explicitly")
