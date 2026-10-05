from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.backtest.model import HistoricalOrderBookObservation
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


@dataclass(frozen=True, slots=True)
class CompactBookEvidence:
    source_bid_levels: int
    source_ask_levels: int
    compact_bid_levels: int
    compact_ask_levels: int
    retained_bid_quantity: Decimal
    retained_ask_quantity: Decimal
    preserve_base_quantity: Decimal


def compact_order_book_observation(
    observation: HistoricalOrderBookObservation,
    *,
    preserve_base_quantity: Decimal,
) -> tuple[HistoricalOrderBookObservation, CompactBookEvidence]:
    if preserve_base_quantity <= 0:
        raise ValueError("preserve_base_quantity must be positive")

    bids, retained_bid = _retain_levels(
        observation.book.bids,
        preserve_base_quantity,
        side="bids",
    )
    asks, retained_ask = _retain_levels(
        observation.book.asks,
        preserve_base_quantity,
        side="asks",
    )
    compact_book = OrderBook(
        bids=bids,
        asks=asks,
        observed_at=observation.book.observed_at,
    )
    compact = HistoricalOrderBookObservation(
        instrument_id=observation.instrument_id,
        action=observation.action,
        source_line=observation.source_line,
        observed_at=observation.observed_at,
        book=compact_book,
    )
    return (
        compact,
        CompactBookEvidence(
            source_bid_levels=len(observation.book.bids),
            source_ask_levels=len(observation.book.asks),
            compact_bid_levels=len(bids),
            compact_ask_levels=len(asks),
            retained_bid_quantity=retained_bid,
            retained_ask_quantity=retained_ask,
            preserve_base_quantity=preserve_base_quantity,
        ),
    )


def _retain_levels(
    levels: tuple[OrderBookLevel, ...],
    minimum_quantity: Decimal,
    *,
    side: str,
) -> tuple[tuple[OrderBookLevel, ...], Decimal]:
    selected: list[OrderBookLevel] = []
    total = Decimal(0)
    for level in levels:
        selected.append(level)
        total += level.quantity
        if total >= minimum_quantity:
            return tuple(selected), total
    raise ValueError(
        f"{side} depth {total} is below required quantity {minimum_quantity}"
    )
