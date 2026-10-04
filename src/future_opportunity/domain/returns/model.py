from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ReturnAttribution:
    funding: Decimal = Decimal(0)
    basis_convergence: Decimal = Decimal(0)
    trading_fees: Decimal = Decimal(0)
    slippage: Decimal = Decimal(0)
    rebalancing_cost: Decimal = Decimal(0)
    residual_directional_pnl: Decimal = Decimal(0)
    unassessed_components: tuple[str, ...] = ()

    @property
    def net_pnl(self) -> Decimal:
        """Sum of assessed return components only."""
        return (
            self.funding
            + self.basis_convergence
            + self.residual_directional_pnl
            - self.trading_fees
            - self.slippage
            - self.rebalancing_cost
        )

    @property
    def complete(self) -> bool:
        return not self.unassessed_components
