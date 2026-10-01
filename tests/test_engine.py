from forex_bot.config import Settings
from forex_bot.engine import TradingEngine


def test_cycle_opens_at_most_risk_limited_position(tmp_path) -> None:
    settings = Settings(state_path=tmp_path / "state.json", min_r2=0, min_slope=0, auto_trade=False)
    result = TradingEngine(settings).run_cycle()
    position = result["state"]["position"]
    assert result["action"] == "opened"
    assert position["units"] <= settings.max_position_units
    assert (
        position["entry_price"] - position["stop_loss"]
    ) / settings.pip_size >= settings.stop_loss_pips - 1e-9
