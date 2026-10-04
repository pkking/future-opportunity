from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from future_opportunity.domain.execution.model import Fill, FillSource
from future_opportunity.domain.market.snapshot import OrderBook


BPS = Decimal(10_000)


class InsufficientLiquidity(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PaperExecutionResult:
    fill: Fill


def _walk(book: OrderBook, side: str, quantity: Decimal) -> tuple[Decimal, Decimal]:
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    levels = book.asks if side == "buy" else book.bids
    remaining = quantity
    total_notional = Decimal(0)

    for level in levels:
        take = min(remaining, level.quantity)
        total_notional += take * level.price
        remaining -= take
        if remaining == 0:
            break

    if remaining > 0:
        raise InsufficientLiquidity(f"missing liquidity for {remaining} units")

    return total_notional / quantity, total_notional


def simulate_market_fill(
    instrument_id: str,
    side: str,
    quantity: Decimal,
    book: OrderBook,
    fee_bps: Decimal,
) -> PaperExecutionResult:
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")

    price, notional = _walk(book, side, quantity)
    reference = book.best_ask if side == "buy" else book.best_bid
    impact = (
        (price / reference - Decimal(1))
        if side == "buy"
        else (Decimal(1) - price / reference)
    )
    slippage_bps = impact * BPS

    return PaperExecutionResult(
        fill=Fill(
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
            price=price,
            notional=notional,
            fee=notional * fee_bps / BPS,
            slippage_bps=slippage_bps,
            filled_at=datetime.now(UTC),
            source=FillSource.SIMULATED,
        )
    )
