from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.application.repositories import SimulationRecord
from future_opportunity.domain.market.liquidity import BPS, estimate_market_fill
from future_opportunity.domain.market.snapshot import OrderBook
from future_opportunity.domain.returns.model import ReturnAttribution


@dataclass(frozen=True, slots=True)
class CloseableValuation:
    attribution: ReturnAttribution
    exit_fees: Decimal
    exit_slippage: Decimal


def assess_closeable_return(
    record: SimulationRecord,
    books: dict[str, OrderBook],
    *,
    unassessed_components: tuple[str, ...] = (),
) -> CloseableValuation:
    policy = record.plan.execution_cost_policy
    if policy is None:
        raise ValueError("strategy plan has no execution cost policy")

    fills = {fill.instrument_id: fill for fill in record.execution.fills}
    plan_legs = {leg.instrument_id: leg for leg in record.plan.legs}

    basis_pnl = Decimal(0)
    exit_fees = Decimal(0)
    exit_slippage = Decimal(0)

    for leg in record.position.legs:
        entry_fill = fills.get(leg.instrument_id)
        plan_leg = plan_legs.get(leg.instrument_id)
        book = books.get(leg.instrument_id)
        if entry_fill is None or plan_leg is None or book is None:
            raise ValueError(f"missing valuation evidence for {leg.instrument_id}")

        quantity = abs(leg.quantity)
        is_spot = plan_leg.id == "spot-leg"

        if leg.quantity > 0:
            reference = book.best_bid
            estimate = estimate_market_fill(book, "sell", quantity)
            basis_pnl += quantity * (reference - entry_fill.reference_price)
            exit_slippage += quantity * reference - estimate.notional
        else:
            reference = book.best_ask
            estimate = estimate_market_fill(book, "buy", quantity)
            basis_pnl += quantity * (entry_fill.reference_price - reference)
            exit_slippage += estimate.notional - quantity * reference

        fee_bps = (
            policy.spot_exit_fee_bps
            if is_spot
            else policy.derivative_exit_fee_bps
        )
        exit_fees += estimate.notional * fee_bps / BPS

    attribution = ReturnAttribution(
        funding=record.current_return.funding,
        basis_convergence=basis_pnl,
        trading_fees=record.entry_return.trading_fees + exit_fees,
        slippage=record.entry_return.slippage + exit_slippage,
        rebalancing_cost=record.current_return.rebalancing_cost,
        residual_directional_pnl=record.current_return.residual_directional_pnl,
        unassessed_components=unassessed_components,
    )
    return CloseableValuation(
        attribution=attribution,
        exit_fees=exit_fees,
        exit_slippage=exit_slippage,
    )
