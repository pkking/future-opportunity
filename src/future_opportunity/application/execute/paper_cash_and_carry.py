from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.adapters.execution.paper import simulate_market_fill
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot
from future_opportunity.domain.position.model import LegPosition, Position, PositionState
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
    cash_and_carry_allocation,
)


@dataclass(frozen=True, slots=True)
class PaperCashAndCarryResult:
    position: Position
    spot_fee: Decimal
    futures_fee: Decimal
    entry_slippage_bps: Decimal


def execute_paper_cash_and_carry(
    position_id: str,
    strategy_plan_id: str,
    snapshot: CashAndCarryMarketSnapshot,
    capital: Decimal,
    assumptions: CashAndCarryAssumptions,
) -> PaperCashAndCarryResult:
    allocation = cash_and_carry_allocation(snapshot, capital, assumptions)
    quantity = allocation.spot_notional / snapshot.spot_book.best_ask

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

    base_delta = spot.quantity - future.quantity
    delta_notional = base_delta * snapshot.spot_book.best_ask
    delta_pct = delta_notional / capital

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
    )

    return PaperCashAndCarryResult(
        position=position,
        spot_fee=spot.fee,
        futures_fee=future.fee,
        entry_slippage_bps=spot.slippage_bps + future.slippage_bps,
    )
