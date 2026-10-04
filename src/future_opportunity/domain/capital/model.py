from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class IsolatedHedgeAllocation:
    total_capital: Decimal
    reserve_amount: Decimal
    spot_notional: Decimal
    hedge_notional: Decimal
    futures_margin: Decimal
    reserve_ratio: Decimal
    futures_leverage: Decimal
    hedge_notional_ratio: Decimal

    @property
    def hedged_notional(self) -> Decimal:
        """Backward-compatible name for the spot-side target notional."""
        return self.spot_notional


def allocate_isolated_hedge(
    capital: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
    hedge_notional_ratio: Decimal = Decimal(1),
) -> IsolatedHedgeAllocation:
    """Allocate capital according to ADR-0001.

    hedge_notional_ratio is hedge quote-notional / spot quote-notional for
    an equal-base-quantity hedge. This matters for dated futures with basis.
    """
    if capital <= 0:
        raise ValueError("capital must be positive")
    if not Decimal(0) <= reserve_ratio < Decimal(1):
        raise ValueError("reserve_ratio must be within [0, 1)")
    if futures_leverage <= 0:
        raise ValueError("futures_leverage must be positive")
    if hedge_notional_ratio <= 0:
        raise ValueError("hedge_notional_ratio must be positive")

    reserve_amount = capital * reserve_ratio
    usable_capital = capital - reserve_amount
    capital_per_spot_notional = (
        Decimal(1) + hedge_notional_ratio / futures_leverage
    )
    spot_notional = usable_capital / capital_per_spot_notional
    hedge_notional = spot_notional * hedge_notional_ratio
    futures_margin = hedge_notional / futures_leverage

    return IsolatedHedgeAllocation(
        total_capital=capital,
        reserve_amount=reserve_amount,
        spot_notional=spot_notional,
        hedge_notional=hedge_notional,
        futures_margin=futures_margin,
        reserve_ratio=reserve_ratio,
        futures_leverage=futures_leverage,
        hedge_notional_ratio=hedge_notional_ratio,
    )
