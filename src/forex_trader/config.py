from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Config:
    values: dict[str, Any]

    def section(self, name: str) -> dict[str, Any]:
        return self.values[name]

    @property
    def pip_size(self) -> float:
        return float(self.values["market"]["pip_size"])


def load_config(path: str | Path) -> Config:
    values = yaml.safe_load(Path(path).read_text())
    required = {
        "market",
        "timeframes",
        "features",
        "model",
        "barriers",
        "decision",
        "execution",
        "risk",
        "costs",
        "backtest",
    }
    missing = required - values.keys()
    if missing:
        raise ValueError(f"Missing configuration sections: {sorted(missing)}")
    if values["market"]["execution_mode"] not in {"BACKTEST", "PAPER", "LIVE"}:
        raise ValueError("execution_mode must be BACKTEST, PAPER, or LIVE")
    return Config(values)
