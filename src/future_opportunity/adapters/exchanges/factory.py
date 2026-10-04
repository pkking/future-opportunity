from __future__ import annotations

from future_opportunity.adapters.exchanges.binance.market_data import BinanceFundingMarketData
from future_opportunity.adapters.exchanges.okx.market_data import OkxFundingMarketData
from future_opportunity.application.ports import FundingCarryMarketDataPort


def funding_market_data_for(venue: str) -> FundingCarryMarketDataPort:
    normalized = venue.lower()
    if normalized == "binance":
        return BinanceFundingMarketData()
    if normalized == "okx":
        return OkxFundingMarketData()
    raise ValueError(f"unsupported venue: {venue}")
