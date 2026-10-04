from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.adapters.execution.paper import simulate_market_fill
from future_opportunity.domain.market.snapshot import FundingCarryMarketSnapshot
from future_opportunity.domain.position.model import LegPosition, Position, PositionState
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    target_hedged_notional,
)


@dataclass(frozen=True, slots=True)
class PaperFundingCarryResult:
    position: Position
    spot_fee: Decimal
    perpetual_fee: Decimal
    entry_slippage_bps: Decimal


def execute_paper_funding_carry(
    position_id: str,
    strategy_plan_id: str,
    snapshot: FundingCarryMarketSnapshot,
    capital: Decimal,
    assumptions: FundingCarryAssumptions,
) -> PaperFundingCarryResult:
    target_notional = target_hedged_notional(capital, assumptions)
    spot_quantity = target_notional / snapshot.spot_book.best_ask

    spot = simulate_market_fill(
        instrument_id=snapshot.spot_instrument_id,
        side="buy",
        quantity=spot_quantity,
        book=snapshot.spot_book,
        fee_bps=assumptions.spot_taker_fee_bps,
    ).fill

    perpetual = simulate_market_fill(
        instrument_id=snapshot.perpetual_instrument_id,
        side="sell",
        quantity=spot.quantity,
        book=snapshot.perpetual_book,
        fee_bps=assumptions.perpetual_taker_fee_bps,
    ).fill

    base_delta = spot.quantity - perpetual.quantity
    delta_notional = base_delta * snapshot.mark_price
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
                instrument_id=perpetual.instrument_id,
                quantity=-perpetual.quantity,
                notional=-perpetual.notional,
            ),
        ),
        delta_notional=delta_notional,
        delta_pct=delta_pct,
    )

    return PaperFundingCarryResult(
        position=position,
        spot_fee=spot.fee,
        perpetual_fee=perpetual.fee,
        entry_slippage_bps=spot.slippage_bps + perpetual.slippage_bps,
    )
