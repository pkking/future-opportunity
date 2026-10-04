from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class IsolatedHedgeAllocation:
    total_capital: Decimal
    reserve_amount: Decimal
    hedged_notional: Decimal
    futures_margin: Decimal
    reserve_ratio: Decimal
    futures_leverage: Decimal


def allocate_isolated_hedge(
    capital: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
) -> IsolatedHedgeAllocation:
    """Allocate capital according to ADR-0001.

    The spot purchase and futures margin must both fit inside usable capital.
    """
    if capital <= 0:
        raise ValueError("capital must be positive")
    if not Decimal(0) <= reserve_ratio < Decimal(1):
        raise ValueError("reserve_ratio must be within [0, 1)")
    if futures_leverage <= 0:
        raise ValueError("futures_leverage must be positive")

    reserve_amount = capital * reserve_ratio
    usable_capital = capital - reserve_amount
    capital_per_notional = Decimal(1) + Decimal(1) / futures_leverage
    hedged_notional = usable_capital / capital_per_notional
    futures_margin = hedged_notional / futures_leverage

    return IsolatedHedgeAllocation(
        total_capital=capital,
        reserve_amount=reserve_amount,
        hedged_notional=hedged_notional,
        futures_margin=futures_margin,
        reserve_ratio=reserve_ratio,
        futures_leverage=futures_leverage,
    )
