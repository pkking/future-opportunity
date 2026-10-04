from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.domain.market.snapshot import OrderBook


BPS = Decimal(10_000)


class InsufficientLiquidity(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MarketFillEstimate:
    price: Decimal
    notional: Decimal
    impact_bps: Decimal


def estimate_market_fill(
    book: OrderBook,
    side: str,
    quantity: Decimal,
) -> MarketFillEstimate:
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
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

    price = total_notional / quantity
    reference = book.best_ask if side == "buy" else book.best_bid
    impact = (
        price / reference - Decimal(1)
        if side == "buy"
        else Decimal(1) - price / reference
    )

    return MarketFillEstimate(
        price=price,
        notional=total_notional,
        impact_bps=impact * BPS,
    )
