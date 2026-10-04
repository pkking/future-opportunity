from __future__ import annotations

from future_opportunity.adapters.exchanges.binance.market_data import BinanceFundingMarketData
from future_opportunity.adapters.exchanges.okx.cash_and_carry import OkxCashAndCarryMarketData
from future_opportunity.adapters.exchanges.okx.market_data import OkxFundingMarketData
from future_opportunity.application.ports import FundingCarryMarketDataPort


def funding_market_data_for(venue: str) -> FundingCarryMarketDataPort:
    normalized = venue.lower()
    if normalized == "binance":
        return BinanceFundingMarketData()
    if normalized == "okx":
        return OkxFundingMarketData()
    raise ValueError(f"unsupported venue: {venue}")


def cash_and_carry_market_data_for(venue: str) -> OkxCashAndCarryMarketData:
    normalized = venue.lower()
    if normalized == "okx":
        return OkxCashAndCarryMarketData()
    raise ValueError(f"cash-and-carry is not supported on venue: {venue}")
