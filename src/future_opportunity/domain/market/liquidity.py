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


def max_visible_quantity_at_impact(
    book: OrderBook,
    side: str,
    max_impact_bps: Decimal,
) -> Decimal:
    """Maximum visible-book quantity whose VWAP impact stays within a threshold."""
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
    if max_impact_bps < 0:
        raise ValueError("max_impact_bps must be non-negative")

    levels = book.asks if side == "buy" else book.bids
    if not levels:
        return Decimal(0)

    reference = book.best_ask if side == "buy" else book.best_bid
    threshold = max_impact_bps / BPS
    target = (
        reference * (Decimal(1) + threshold)
        if side == "buy"
        else reference * (Decimal(1) - threshold)
    )

    quantity = Decimal(0)
    notional = Decimal(0)

    for level in levels:
        whole_quantity = quantity + level.quantity
        whole_notional = notional + level.quantity * level.price
        whole_vwap = whole_notional / whole_quantity
        within = whole_vwap <= target if side == "buy" else whole_vwap >= target

        if within:
            quantity = whole_quantity
            notional = whole_notional
            continue

        if side == "buy":
            denominator = level.price - target
            numerator = target * quantity - notional
        else:
            denominator = target - level.price
            numerator = notional - target * quantity

        if denominator <= 0 or numerator <= 0:
            break

        partial = min(level.quantity, numerator / denominator)
        quantity += partial
        break

    return quantity
