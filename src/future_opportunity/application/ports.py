from __future__ import annotations

from typing import Protocol

from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    FundingCarryMarketSnapshot,
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
