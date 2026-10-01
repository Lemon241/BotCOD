from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    symbol: str = "EUR_USD"
    initial_balance: float = Field(10_000, gt=0)
    risk_per_trade: float = Field(0.005, gt=0, le=0.02)
    max_position_units: int = Field(100_000, gt=0)
    stop_loss_pips: float = Field(20, gt=0)
    take_profit_pips: float = Field(40, gt=0)
    lookback: int = Field(30, ge=5)
    min_slope: float = Field(0.00001, ge=0)
    min_r2: float = Field(0.35, ge=0, le=1)
    spread_pips: float = Field(1.0, ge=0)
    slippage_pips: float = Field(0.2, ge=0)
    cycle_seconds: int = Field(60, ge=5)
    auto_trade: bool = True
    data_csv: Path | None = None
    state_path: Path = Path("data/state.json")

    @property
    def pip_size(self) -> float:
        return 0.01 if "JPY" in self.symbol.upper() else 0.0001
