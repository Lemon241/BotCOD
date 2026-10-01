#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from forex_trader.backtest.engine import BacktestEngine
from forex_trader.config import load_config
from forex_trader.data.pipeline import build_timeframes, load_market_data, temporal_split
from forex_trader.decision.rule_based import RuleBasedDecisionEngine
from forex_trader.domain.models import Prediction
from forex_trader.features.pipeline import build_features, market_context
from forex_trader.labels.barrier import Outcome, build_barrier_labels
from forex_trader.models.baseline import ProbabilityModel
from forex_trader.monitoring.report import write_report


def synthetic(periods=5000):
    rng = np.random.default_rng(42)
    close = 1.08 + np.cumsum(rng.normal(0, 0.00008, periods))
    idx = pd.date_range("2024-01-01", periods=periods, freq="min", tz="UTC")
    spread = rng.uniform(0.5, 1.2, periods)
    return pd.DataFrame(
        {
            "open": np.r_[close[0], close[:-1]],
            "high": close + 0.0001,
            "low": close - 0.0001,
            "close": close,
            "spread": spread,
            "tick_volume": rng.integers(10, 100, periods),
        },
        index=idx,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/research.yaml")
    parser.add_argument("--data")
    args = parser.parse_args()
    config = load_config(args.config)
    m1 = load_market_data(args.data) if args.data else synthetic()
    frames = build_timeframes(m1)
    m5 = frames["m5"]
    features = build_features(m5)
    labels = build_barrier_labels(
        m5,
        features.atr_14,
        config.section("barriers")["take_profit_atr"],
        config.section("barriers")["stop_loss_atr"],
        3,
        config.section("backtest")["ambiguous_policy"],
    )
    dataset = features.join(labels).dropna()
    train, val, test = temporal_split(
        dataset, config.section("backtest")["train_fraction"], config.section("backtest")["validation_fraction"]
    )
    columns = [c for c in features if c in dataset]

    def fit(direction):
        target = f"{direction}_outcome"
        model = ProbabilityModel(
            config.section("model")["type"],
            config.section("model")["calibration"],
            config.section("model")["random_seed"],
        )
        return model.fit(
            train[columns],
            (train[target] == Outcome.TP_FIRST).astype(int),
            val[columns],
            (val[target] == Outcome.TP_FIRST).astype(int),
        )

    long_model, short_model = fit("long"), fit("short")
    pl = long_model.predict_proba(test[columns])
    ps = short_model.predict_proba(test[columns])
    d = config.section("decision")
    b = config.section("barriers")
    e = config.section("execution")
    c = config.section("costs")
    signals = []
    for i, timestamp in enumerate(test.index):
        context = market_context(frames["m15"].loc[:timestamp])
        spread = float(m5.loc[timestamp].get("spread", c["default_spread_pips"]))
        if b["mode"] == "atr":
            atr_pips = float(test.loc[timestamp, "atr_14"] / config.pip_size)
            tp_pips = atr_pips * b["take_profit_atr"]
            sl_pips = atr_pips * b["stop_loss_atr"]
        else:
            tp_pips, sl_pips = b["take_profit_pips"], b["stop_loss_pips"]
        engine = RuleBasedDecisionEngine(
            config.section("model")["min_probability"],
            d["min_expected_value_pips"],
            d["min_ev_difference_pips"],
            tp_pips,
            sl_pips,
            e["max_spread_pips"],
            c["slippage_pips"],
            counter_trend_factor=d["counter_trend_factor"],
        )
        prediction = Prediction(timestamp.to_pydatetime(), float(pl[i]), float(ps[i]))
        decision = engine.decide(prediction, context, spread)
        signals.append(
            {
                "timestamp": timestamp,
                "action": decision.action,
                "p_long_success": float(pl[i]),
                "p_short_success": float(ps[i]),
                "p_success": decision.p_success,
                "expected_value": decision.expected_value,
                "take_profit": decision.take_profit,
                "stop_loss": decision.stop_loss,
                "m15_regime": context.market_regime,
                "model_version": "baseline-v1",
            }
        )
    predictions = pd.DataFrame(signals)
    trades, equity, metrics = BacktestEngine(config).run(m1, signals)
    write_report(config.section("backtest")["output_dir"], trades, predictions, equity, metrics, config.values)
    print(metrics)


if __name__ == "__main__":
    main()
