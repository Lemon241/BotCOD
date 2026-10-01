import pandas as pd

from forex_trader.labels.barrier import Outcome, barrier_outcome


def test_known_barrier_outcomes():
    tp = pd.DataFrame([{"high": 1.002, "low": 1.0}])
    sl = pd.DataFrame([{"high": 1.0, "low": 0.998}])
    ambiguous = pd.DataFrame([{"high": 1.002, "low": 0.998}])
    flat = pd.DataFrame([{"high": 1.0001, "low": 0.9999}])
    assert barrier_outcome(tp, "LONG", 1, 0.001, 0.001) == Outcome.TP_FIRST
    assert barrier_outcome(sl, "LONG", 1, 0.001, 0.001) == Outcome.SL_FIRST
    assert barrier_outcome(ambiguous, "LONG", 1, 0.001, 0.001) == Outcome.SL_FIRST
    assert barrier_outcome(ambiguous, "LONG", 1, 0.001, 0.001, "discard") == Outcome.AMBIGUOUS
    assert barrier_outcome(flat, "LONG", 1, 0.001, 0.001) == Outcome.TIMEOUT
