from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OrderBookLevel:
    price: Decimal
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class OrderBook:
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    observed_at: datetime

    @property
    def best_bid(self) -> Decimal:
        if not self.bids:
            raise ValueError("order book has no bids")
        return self.bids[0].price

    @property
    def best_ask(self) -> Decimal:
        if not self.asks:
            raise ValueError("order book has no asks")
        return self.asks[0].price


@dataclass(frozen=True, slots=True)
class FundingObservation:
    rate: Decimal
    funding_time: datetime
    mark_price: Decimal | None = None
    rate_type: str | None = None


@dataclass(frozen=True, slots=True)
class FundingCarryMarketSnapshot:
    venue: str
    base: str
    quote: str
    spot_instrument_id: str
    perpetual_instrument_id: str
    spot_book: OrderBook
    perpetual_book: OrderBook
    mark_price: Decimal
    last_funding_rate: Decimal
    next_funding_time: datetime
    funding_history: tuple[FundingObservation, ...]
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class CashAndCarryMarketSnapshot:
    venue: str
    base: str
    quote: str
    spot_instrument_id: str
    future_instrument_id: str
    spot_book: OrderBook
    future_book: OrderBook
    expiry: datetime
    observed_at: datetime
