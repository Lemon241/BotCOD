#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from forex_trader.data.pipeline import build_timeframes, load_market_data
from forex_trader.features.pipeline import build_features

p = argparse.ArgumentParser()
p.add_argument("input")
p.add_argument("output")
a = p.parse_args()
build_features(build_timeframes(load_market_data(a.input))["m5"]).to_csv(a.output)
