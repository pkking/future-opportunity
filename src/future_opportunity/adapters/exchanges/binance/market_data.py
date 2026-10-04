from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx

from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)


class BinanceFundingMarketData:
    """Read-only Binance spot + USD-M perpetual market data adapter."""

    SPOT_BASE_URL = "https://data-api.binance.vision"
    FUTURES_BASE_URL = "https://fapi.binance.com"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._timeout = timeout_seconds

    async def snapshot(self, base: str, quote: str = "USDT") -> FundingCarryMarketSnapshot:
        symbol = f"{base.upper()}{quote.upper()}"
        now = datetime.now(UTC)
        start_time_ms = int((now - timedelta(days=30)).timestamp() * 1000)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            spot_depth, perpetual_depth, premium, funding = await asyncio.gather(
                self._get(
                    client,
                    f"{self.SPOT_BASE_URL}/api/v3/depth",
                    {"symbol": symbol, "limit": 100},
                ),
                self._get(
                    client,
                    f"{self.FUTURES_BASE_URL}/fapi/v1/depth",
                    {"symbol": symbol, "limit": 100},
                ),
                self._get(
                    client,
                    f"{self.FUTURES_BASE_URL}/fapi/v1/premiumIndex",
                    {"symbol": symbol},
                ),
                self._get(
                    client,
                    f"{self.FUTURES_BASE_URL}/fapi/v1/fundingRate",
                    {"symbol": symbol, "startTime": start_time_ms, "limit": 1000},
                ),
            )

        observed_at = datetime.now(UTC)

        return FundingCarryMarketSnapshot(
            venue="binance",
            base=base.upper(),
            quote=quote.upper(),
            spot_instrument_id=f"binance:{symbol}:spot",
            perpetual_instrument_id=f"binance:{symbol}:perpetual",
            spot_book=self._parse_book(spot_depth, observed_at),
            perpetual_book=self._parse_book(perpetual_depth, observed_at),
            mark_price=Decimal(premium["markPrice"]),
            last_funding_rate=Decimal(premium["lastFundingRate"]),
            next_funding_time=datetime.fromtimestamp(
                int(premium["nextFundingTime"]) / 1000,
                tz=UTC,
            ),
            funding_history=self._parse_funding_history(funding),
            observed_at=observed_at,
        )

    @staticmethod
    async def _get(
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, str | int],
    ) -> object:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _parse_book(payload: object, observed_at: datetime) -> OrderBook:
        if not isinstance(payload, dict):
            raise TypeError("unexpected order book response")

        bids = tuple(
            OrderBookLevel(price=Decimal(price), quantity=Decimal(quantity))
            for price, quantity in payload.get("bids", [])
        )
        asks = tuple(
            OrderBookLevel(price=Decimal(price), quantity=Decimal(quantity))
            for price, quantity in payload.get("asks", [])
        )
        return OrderBook(bids=bids, asks=asks, observed_at=observed_at)


    @staticmethod
    def _parse_funding_history(payload: object) -> tuple[FundingObservation, ...]:
        if not isinstance(payload, list):
            raise TypeError("unexpected Binance funding history response")

        return tuple(
            FundingObservation(
                rate=Decimal(item["fundingRate"]),
                funding_time=datetime.fromtimestamp(
                    int(item["fundingTime"]) / 1000,
                    tz=UTC,
                ),
                mark_price=(
                    Decimal(item["markPrice"])
                    if item.get("markPrice")
                    else None
                ),
                rate_type=item.get("rateType"),
            )
            for item in payload
        )
