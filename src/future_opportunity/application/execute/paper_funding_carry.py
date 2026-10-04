from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.adapters.execution.paper import simulate_market_fill
from future_opportunity.domain.capital.model import allocate_isolated_hedge
from future_opportunity.domain.deployment.model import DeploymentAssessment
from future_opportunity.domain.execution.model import Fill
from future_opportunity.domain.market.snapshot import FundingCarryMarketSnapshot
from future_opportunity.domain.position.model import LegPosition, Position, PositionState
from future_opportunity.domain.returns.model import ReturnAttribution
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


@dataclass(frozen=True, slots=True)
class PaperFundingCarryResult:
    position: Position
    fills: tuple[Fill, Fill]
    entry_return: ReturnAttribution

    @property
    def spot_fee(self) -> Decimal:
        return self.fills[0].fee

    @property
    def perpetual_fee(self) -> Decimal:
        return self.fills[1].fee

    @property
    def entry_slippage_bps(self) -> Decimal:
        return self.fills[0].slippage_bps + self.fills[1].slippage_bps


def execute_paper_funding_carry(
    position_id: str,
    strategy_plan_id: str,
    snapshot: FundingCarryMarketSnapshot,
    capital: Decimal,
    assumptions: FundingCarryAssumptions,
    deployment: DeploymentAssessment | None = None,
) -> PaperFundingCarryResult:
    target_notional = (
        deployment.actual_spot_notional
        if deployment is not None
        else allocate_isolated_hedge(
            capital,
            assumptions.reserve_ratio,
            assumptions.futures_leverage,
        ).hedged_notional
    )
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

    if deployment is not None:
        max_impact = deployment.max_impact_bps
        if spot.slippage_bps > max_impact or perpetual.slippage_bps > max_impact:
            raise ValueError("entry fill exceeds frozen liquidity impact limit")

    base_delta = spot.quantity - perpetual.quantity
    delta_notional = base_delta * snapshot.mark_price
    delta_pct = delta_notional / capital

    entry_return = ReturnAttribution(
        trading_fees=spot.fee + perpetual.fee,
        slippage=spot.slippage_quote + perpetual.slippage_quote,
    )
    opened_at = max(spot.filled_at, perpetual.filled_at)

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
        realized_pnl=entry_return.net_pnl,
        opened_at=opened_at,
    )

    return PaperFundingCarryResult(
        position=position,
        fills=(spot, perpetual),
        entry_return=entry_return,
    )
