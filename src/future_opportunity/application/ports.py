from __future__ import annotations

from typing import Protocol

from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    DeliverySettlement,
    FundingCarryMarketSnapshot,
    OrderBook,
)


class FundingCarryMarketDataPort(Protocol):
    async def snapshot(self, base: str, quote: str = "USDT") -> FundingCarryMarketSnapshot:
        """Return a canonical, read-only spot/perpetual market snapshot."""
        ...


class CashAndCarryMarketDataPort(Protocol):
    async def snapshots(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[CashAndCarryMarketSnapshot, ...]:
        """Return live dated-future candidates with normalized base quantities."""
        ...

    async def spot_book(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[str, OrderBook]:
        """Return the canonical spot instrument id and current spot book."""
        ...

    async def delivery_settlement(
        self,
        future_instrument_id: str,
        base: str,
        quote: str = "USDT",
    ) -> DeliverySettlement | None:
        """Return public expiry settlement evidence when the future has delivered."""
        ...
