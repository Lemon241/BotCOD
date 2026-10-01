from enum import StrEnum

import pandas as pd


class Outcome(StrEnum):
    TP_FIRST = "TP_FIRST"
    SL_FIRST = "SL_FIRST"
    TIMEOUT = "TIMEOUT"
    AMBIGUOUS = "AMBIGUOUS"


def barrier_outcome(
    future: pd.DataFrame, direction: str, entry: float, tp: float, sl: float, ambiguous_policy: str = "assume_loss"
) -> Outcome:
    for _, candle in future.iterrows():
        tp_hit = candle.high >= entry + tp if direction == "LONG" else candle.low <= entry - tp
        sl_hit = candle.low <= entry - sl if direction == "LONG" else candle.high >= entry + sl
        if tp_hit and sl_hit:
            return Outcome.SL_FIRST if ambiguous_policy == "assume_loss" else Outcome.AMBIGUOUS
        if sl_hit:
            return Outcome.SL_FIRST
        if tp_hit:
            return Outcome.TP_FIRST
    return Outcome.TIMEOUT


def barrier_event(
    future: pd.DataFrame,
    direction: str,
    entry: float,
    tp: float,
    sl: float,
    ambiguous_policy: str = "assume_loss",
) -> tuple[Outcome, pd.Timestamp]:
    """Resolve the first barrier chronologically and return its candle timestamp."""
    if future.empty:
        raise ValueError("Barrier horizon cannot be empty")
    for timestamp in future.index:
        outcome = barrier_outcome(future.loc[[timestamp]], direction, entry, tp, sl, ambiguous_policy)
        if outcome != Outcome.TIMEOUT:
            return outcome, timestamp
    return Outcome.TIMEOUT, future.index[-1]


def build_barrier_labels(
    frame: pd.DataFrame, atr: pd.Series, tp_atr: float, sl_atr: float, horizon: int, policy: str = "assume_loss"
) -> pd.DataFrame:
    rows = []
    for i in range(len(frame)):
        if pd.isna(atr.iloc[i]):
            rows.append((None, None))
            continue
        future = frame.iloc[i + 1 : i + 1 + horizon]
        entry = frame.close.iloc[i]
        tp = atr.iloc[i] * tp_atr
        sl = atr.iloc[i] * sl_atr
        rows.append(
            (
                barrier_outcome(future, "LONG", entry, tp, sl, policy),
                barrier_outcome(future, "SHORT", entry, tp, sl, policy),
            )
        )
    return pd.DataFrame(rows, index=frame.index, columns=["long_outcome", "short_outcome"])
