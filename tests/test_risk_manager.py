from datetime import date

from forex_trader.risk.manager import AccountState, RiskManager


def test_position_size_and_circuit_breakers():
    manager = RiskManager(0.25, 1, 1.5, 8)
    state = AccountState(10000, 10000, 10000, date.today(), 10000)
    assert manager.assess(state, 5, 0.0001).units == 50000
    state.equity = 9800
    assert not manager.assess(state, 5, 0.0001).approved
