def position_size(
    balance: float, risk_fraction: float, stop_loss_pips: float, pip_size: float
) -> int:
    """Size assuming account and quote currency coincide (suitable for this paper MVP)."""
    cash_at_risk = balance * risk_fraction
    loss_per_unit = stop_loss_pips * pip_size
    return max(0, int(cash_at_risk / loss_per_unit))
