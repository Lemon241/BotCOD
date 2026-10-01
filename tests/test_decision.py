from datetime import UTC, datetime

from forex_trader.decision.rule_based import RuleBasedDecisionEngine
from forex_trader.domain.models import MarketContext, Prediction


def test_no_trade_is_default_without_edge():
    now = datetime.now(UTC)
    context = MarketContext(now, "BULLISH", 0.5, "NORMAL", "TRENDING")
    prediction = Prediction(now, 0.55, 0.45)
    engine = RuleBasedDecisionEngine(0.7, 0.3, 0.1, 8, 5, 1.5, 0.1)
    assert engine.decide(prediction, context, 0.8).action == "NO_TRADE"
