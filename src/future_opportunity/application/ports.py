from __future__ import annotations

from typing import Protocol

from future_opportunity.domain.market.snapshot import FundingCarryMarketSnapshot


class FundingCarryMarketDataPort(Protocol):
    async def snapshot(self, base: str, quote: str = "USDT") -> FundingCarryMarketSnapshot:
        """Return a canonical, read-only spot/perpetual market snapshot."""
        ...
