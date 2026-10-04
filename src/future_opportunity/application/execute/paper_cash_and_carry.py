from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.adapters.execution.paper import simulate_market_fill
from future_opportunity.domain.deployment.model import DeploymentAssessment
from future_opportunity.domain.execution.model import Fill
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot
from future_opportunity.domain.position.model import LegPosition, Position, PositionState
from future_opportunity.domain.returns.model import ReturnAttribution
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
    cash_and_carry_allocation,
)


@dataclass(frozen=True, slots=True)
class PaperCashAndCarryResult:
    position: Position
    fills: tuple[Fill, Fill]
    entry_return: ReturnAttribution

    @property
    def spot_fee(self) -> Decimal:
        return self.fills[0].fee

    @property
    def futures_fee(self) -> Decimal:
        return self.fills[1].fee

    @property
    def entry_slippage_bps(self) -> Decimal:
        return self.fills[0].slippage_bps + self.fills[1].slippage_bps


def execute_paper_cash_and_carry(
    position_id: str,
    strategy_plan_id: str,
    snapshot: CashAndCarryMarketSnapshot,
    capital: Decimal,
    assumptions: CashAndCarryAssumptions,
    deployment: DeploymentAssessment | None = None,
) -> PaperCashAndCarryResult:
    allocation = cash_and_carry_allocation(snapshot, capital, assumptions)
    spot_notional = (
        deployment.actual_spot_notional
        if deployment is not None
        else allocation.spot_notional
    )
    quantity = spot_notional / snapshot.spot_book.best_ask

    spot = simulate_market_fill(
        instrument_id=snapshot.spot_instrument_id,
        side="buy",
        quantity=quantity,
        book=snapshot.spot_book,
        fee_bps=assumptions.spot_entry_fee_bps,
    ).fill
    future = simulate_market_fill(
        instrument_id=snapshot.future_instrument_id,
        side="sell",
        quantity=spot.quantity,
        book=snapshot.future_book,
        fee_bps=assumptions.futures_entry_fee_bps,
    ).fill

    if deployment is not None:
        max_impact = deployment.max_impact_bps
        if spot.slippage_bps > max_impact or future.slippage_bps > max_impact:
            raise ValueError("entry fill exceeds frozen liquidity impact limit")

    base_delta = spot.quantity - future.quantity
    delta_notional = base_delta * snapshot.spot_book.best_ask
    delta_pct = delta_notional / capital

    entry_return = ReturnAttribution(
        trading_fees=spot.fee + future.fee,
        slippage=spot.slippage_quote + future.slippage_quote,
    )
    opened_at = max(spot.filled_at, future.filled_at)

    position = Position(
        id=position_id,
        strategy_plan_id=strategy_plan_id,
        state=PositionState.HEDGED,
        legs=(
            LegPosition(
                instrument_id=spot.instrument_id,
                quantity=spot.quantity,
                notional=spot.notional,
            ),
            LegPosition(
                instrument_id=future.instrument_id,
                quantity=-future.quantity,
                notional=-future.notional,
            ),
        ),
        delta_notional=delta_notional,
        delta_pct=delta_pct,
        realized_pnl=entry_return.net_pnl,
        opened_at=opened_at,
    )

    return PaperCashAndCarryResult(
        position=position,
        fills=(spot, future),
        entry_return=entry_return,
    )
