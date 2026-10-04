from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.domain.capital.model import (
    IsolatedHedgeAllocation,
    allocate_isolated_hedge,
)
from future_opportunity.domain.market.liquidity import (
    BPS,
    estimate_market_fill,
    hedged_visible_spot_notional_capacity,
)
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot


SECONDS_PER_DAY = Decimal(86_400)
DAYS_PER_YEAR = Decimal(365)


@dataclass(frozen=True, slots=True)
class CashAndCarryAssumptions:
    reserve_ratio: Decimal = Decimal("0.10")
    futures_leverage: Decimal = Decimal(1)
    spot_entry_fee_bps: Decimal = Decimal(10)
    futures_entry_fee_bps: Decimal = Decimal(5)
    spot_exit_fee_bps: Decimal = Decimal(10)
    futures_settlement_fee_bps: Decimal = Decimal(5)
    exit_buffer_bps: Decimal = Decimal(5)

    def __post_init__(self) -> None:
        if not Decimal(0) <= self.reserve_ratio < Decimal(1):
            raise ValueError("reserve_ratio must be within [0, 1)")
        if self.futures_leverage <= 0:
            raise ValueError("futures_leverage must be positive")
        for name, value in (
            ("spot_entry_fee_bps", self.spot_entry_fee_bps),
            ("futures_entry_fee_bps", self.futures_entry_fee_bps),
            ("spot_exit_fee_bps", self.spot_exit_fee_bps),
            ("futures_settlement_fee_bps", self.futures_settlement_fee_bps),
            ("exit_buffer_bps", self.exit_buffer_bps),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class CashAndCarryEvaluation:
    venue: str
    base: str
    quote: str
    future_instrument_id: str
    expiry: str
    days_to_expiry: Decimal
    capital: Decimal
    reserve_amount: Decimal
    spot_notional: Decimal
    futures_notional: Decimal
    futures_margin: Decimal
    visible_capacity_5bps: Decimal
    visible_capacity_10bps: Decimal
    gross_basis_return_on_notional: Decimal
    gross_return_to_expiry: Decimal
    assumed_fee_return: Decimal
    estimated_liquidity_cost_return: Decimal
    expected_net_return_to_expiry: Decimal
    annualized_equivalent: Decimal
    return_character: str = "convergent"


def cash_and_carry_allocation(
    snapshot: CashAndCarryMarketSnapshot,
    capital: Decimal,
    assumptions: CashAndCarryAssumptions,
) -> IsolatedHedgeAllocation:
    hedge_ratio = snapshot.future_book.best_bid / snapshot.spot_book.best_ask
    return allocate_isolated_hedge(
        capital,
        assumptions.reserve_ratio,
        assumptions.futures_leverage,
        hedge_notional_ratio=hedge_ratio,
    )


def _annualize(net_return: Decimal, days_to_expiry: Decimal) -> Decimal:
    if days_to_expiry <= 0:
        raise ValueError("future must expire after observation time")
    if net_return <= Decimal(-1):
        raise ValueError("net return must be greater than -100%")
    exponent = DAYS_PER_YEAR / days_to_expiry
    return ((Decimal(1) + net_return).ln() * exponent).exp() - Decimal(1)


def evaluate_cash_and_carry(
    snapshot: CashAndCarryMarketSnapshot,
    capital: Decimal,
    assumptions: CashAndCarryAssumptions,
) -> CashAndCarryEvaluation:
    allocation = cash_and_carry_allocation(snapshot, capital, assumptions)
    quantity = allocation.spot_notional / snapshot.spot_book.best_ask

    spot_entry = estimate_market_fill(snapshot.spot_book, "buy", quantity)
    future_entry = estimate_market_fill(snapshot.future_book, "sell", quantity)

    gross_basis_return_on_notional = (
        snapshot.future_book.best_bid / snapshot.spot_book.best_ask - Decimal(1)
    )
    gross_pnl = quantity * (
        snapshot.future_book.best_bid - snapshot.spot_book.best_ask
    )
    gross_return = gross_pnl / capital

    fee_quote = (
        allocation.spot_notional
        * (assumptions.spot_entry_fee_bps + assumptions.spot_exit_fee_bps)
        / BPS
        + allocation.hedge_notional
        * (
            assumptions.futures_entry_fee_bps
            + assumptions.futures_settlement_fee_bps
        )
        / BPS
    )
    assumed_fee_return = fee_quote / capital

    spot_entry_impact = (
        spot_entry.notional - quantity * snapshot.spot_book.best_ask
    )
    future_entry_impact = (
        quantity * snapshot.future_book.best_bid - future_entry.notional
    )
    exit_buffer = allocation.spot_notional * assumptions.exit_buffer_bps / BPS
    liquidity_cost_return = (
        spot_entry_impact + future_entry_impact + exit_buffer
    ) / capital

    net_return = gross_return - assumed_fee_return - liquidity_cost_return
    seconds_to_expiry = Decimal(
        str((snapshot.expiry - snapshot.observed_at).total_seconds())
    )
    days_to_expiry = seconds_to_expiry / SECONDS_PER_DAY

    return CashAndCarryEvaluation(
        venue=snapshot.venue,
        base=snapshot.base,
        quote=snapshot.quote,
        future_instrument_id=snapshot.future_instrument_id,
        expiry=snapshot.expiry.isoformat(),
        days_to_expiry=days_to_expiry,
        capital=capital,
        reserve_amount=allocation.reserve_amount,
        spot_notional=allocation.spot_notional,
        futures_notional=allocation.hedge_notional,
        futures_margin=allocation.futures_margin,
        visible_capacity_5bps=hedged_visible_spot_notional_capacity(
            snapshot.spot_book,
            snapshot.future_book,
            Decimal(5),
        ),
        visible_capacity_10bps=hedged_visible_spot_notional_capacity(
            snapshot.spot_book,
            snapshot.future_book,
            Decimal(10),
        ),
        gross_basis_return_on_notional=gross_basis_return_on_notional,
        gross_return_to_expiry=gross_return,
        assumed_fee_return=assumed_fee_return,
        estimated_liquidity_cost_return=liquidity_cost_return,
        expected_net_return_to_expiry=net_return,
        annualized_equivalent=_annualize(net_return, days_to_expiry),
    )
