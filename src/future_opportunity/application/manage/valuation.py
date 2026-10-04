from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.adapters.execution.paper import simulate_market_fill
from future_opportunity.application.repositories import SimulationRecord
from future_opportunity.domain.execution.model import Fill, FillSource
from future_opportunity.domain.market.liquidity import BPS, estimate_market_fill
from future_opportunity.domain.market.snapshot import DeliverySettlement, OrderBook
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


@dataclass(frozen=True, slots=True)
class PaperCloseEvidence:
    fills: tuple[Fill, ...]
    attribution: ReturnAttribution


def simulate_close_evidence(
    record: SimulationRecord,
    books: dict[str, OrderBook],
    *,
    unassessed_components: tuple[str, ...] = (),
) -> PaperCloseEvidence:
    policy = record.plan.execution_cost_policy
    if policy is None:
        raise ValueError("strategy plan has no execution cost policy")

    entry_fills = {fill.instrument_id: fill for fill in record.execution.fills}
    plan_legs = {leg.instrument_id: leg for leg in record.plan.legs}

    close_fills: list[Fill] = []
    basis_pnl = Decimal(0)

    for leg in record.position.legs:
        entry_fill = entry_fills.get(leg.instrument_id)
        plan_leg = plan_legs.get(leg.instrument_id)
        book = books.get(leg.instrument_id)
        if entry_fill is None or plan_leg is None or book is None:
            raise ValueError(f"missing close evidence for {leg.instrument_id}")

        quantity = abs(leg.quantity)
        is_spot = plan_leg.id == "spot-leg"
        side = "sell" if leg.quantity > 0 else "buy"
        fee_bps = (
            policy.spot_exit_fee_bps
            if is_spot
            else policy.derivative_exit_fee_bps
        )
        close_fill = simulate_market_fill(
            instrument_id=leg.instrument_id,
            side=side,
            quantity=quantity,
            book=book,
            fee_bps=fee_bps,
        ).fill
        close_fills.append(close_fill)

        if leg.quantity > 0:
            basis_pnl += quantity * (
                close_fill.reference_price - entry_fill.reference_price
            )
        else:
            basis_pnl += quantity * (
                entry_fill.reference_price - close_fill.reference_price
            )

    attribution = ReturnAttribution(
        funding=record.current_return.funding,
        basis_convergence=basis_pnl,
        trading_fees=(
            record.entry_return.trading_fees
            + sum((fill.fee for fill in close_fills), Decimal(0))
        ),
        slippage=(
            record.entry_return.slippage
            + sum((fill.slippage_quote for fill in close_fills), Decimal(0))
        ),
        rebalancing_cost=record.current_return.rebalancing_cost,
        residual_directional_pnl=record.current_return.residual_directional_pnl,
        unassessed_components=unassessed_components,
    )
    return PaperCloseEvidence(
        fills=tuple(close_fills),
        attribution=attribution,
    )


def simulate_delivery_close_evidence(
    record: SimulationRecord,
    *,
    spot_instrument_id: str,
    spot_book: OrderBook,
    settlement: DeliverySettlement,
) -> PaperCloseEvidence:
    """Close spot now while using public delivery evidence for the expired future.

    Basis convergence is frozen from entry spot/future reference prices.
    Any spot move from the delivery price until the paper spot sale is attributed
    to residual directional PnL because the future hedge no longer exists.
    """
    policy = record.plan.execution_cost_policy
    if policy is None:
        raise ValueError("strategy plan has no execution cost policy")

    entry_fills = {fill.instrument_id: fill for fill in record.execution.fills}
    spot_entry = entry_fills.get(spot_instrument_id)
    future_entry = entry_fills.get(settlement.future_instrument_id)
    if spot_entry is None or future_entry is None:
        raise ValueError("missing entry fills for delivery close")

    spot_position = next(
        (
            leg
            for leg in record.position.legs
            if leg.instrument_id == spot_instrument_id
        ),
        None,
    )
    future_position = next(
        (
            leg
            for leg in record.position.legs
            if leg.instrument_id == settlement.future_instrument_id
        ),
        None,
    )
    if spot_position is None or future_position is None:
        raise ValueError("missing position legs for delivery close")
    if spot_position.quantity <= 0 or future_position.quantity >= 0:
        raise ValueError("delivery close expects long spot and short future")

    quantity = spot_position.quantity
    if abs(abs(future_position.quantity) - quantity) > Decimal("1e-18"):
        raise ValueError("delivery close requires equal base-asset quantities")

    spot_close = simulate_market_fill(
        instrument_id=spot_instrument_id,
        side="sell",
        quantity=quantity,
        book=spot_book,
        fee_bps=policy.spot_exit_fee_bps,
    ).fill

    settlement_notional = quantity * settlement.settlement_price
    settlement_fee = (
        settlement_notional * policy.derivative_exit_fee_bps / BPS
    )
    future_settlement = Fill(
        instrument_id=settlement.future_instrument_id,
        side="buy",
        quantity=quantity,
        price=settlement.settlement_price,
        reference_price=settlement.settlement_price,
        notional=settlement_notional,
        fee=settlement_fee,
        slippage_bps=Decimal(0),
        slippage_quote=Decimal(0),
        filled_at=settlement.settled_at,
        source=FillSource.SETTLEMENT,
    )

    basis_convergence = quantity * (
        future_entry.reference_price - spot_entry.reference_price
    )
    residual_directional_pnl = quantity * (
        spot_close.reference_price - settlement.settlement_price
    )

    attribution = ReturnAttribution(
        basis_convergence=basis_convergence,
        trading_fees=(
            record.entry_return.trading_fees
            + spot_close.fee
            + future_settlement.fee
        ),
        slippage=(
            record.entry_return.slippage
            + spot_close.slippage_quote
        ),
        rebalancing_cost=record.current_return.rebalancing_cost,
        residual_directional_pnl=residual_directional_pnl,
    )
    return PaperCloseEvidence(
        fills=(future_settlement, spot_close),
        attribution=attribution,
    )
