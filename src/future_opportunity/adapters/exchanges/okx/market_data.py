from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import httpx

from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)


class OkxFundingMarketData:
    """Read-only OKX spot + USDT perpetual market data adapter."""

    def __init__(
        self,
        base_url: str = "https://www.okx.com",
        timeout_seconds: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def snapshot(self, base: str, quote: str = "USDT") -> FundingCarryMarketSnapshot:
        base = base.upper()
        quote = quote.upper()
        spot_id = f"{base}-{quote}"
        swap_id = f"{base}-{quote}-SWAP"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            spot_book_raw, swap_book_raw, funding_raw, history_raw, instrument_raw = (
                await asyncio.gather(
                    self._get(
                        client,
                        "/api/v5/market/books",
                        {"instId": spot_id, "sz": 100},
                    ),
                    self._get(
                        client,
                        "/api/v5/market/books",
                        {"instId": swap_id, "sz": 100},
                    ),
                    self._get(
                        client,
                        "/api/v5/public/funding-rate",
                        {"instId": swap_id},
                    ),
                    self._get(
                        client,
                        "/api/v5/public/funding-rate-history",
                        {"instId": swap_id, "limit": 400},
                    ),
                    self._get(
                        client,
                        "/api/v5/public/instruments",
                        {"instType": "SWAP", "instId": swap_id},
                    ),
                )
            )

        observed_at = datetime.now(UTC)
        instrument = self._first_data(instrument_raw)
        contract_value = Decimal(instrument["ctVal"])
        contract_value_currency = instrument["ctValCcy"]
        if contract_value_currency != base:
            raise ValueError(
                f"unsupported OKX contract value currency: {contract_value_currency}"
            )

        spot_book = self._parse_book(
            self._first_data(spot_book_raw),
            observed_at,
            quantity_multiplier=Decimal(1),
        )
        swap_book = self._parse_book(
            self._first_data(swap_book_raw),
            observed_at,
            quantity_multiplier=contract_value,
        )

        funding = self._first_data(funding_raw)
        history = self._data(history_raw)

        return FundingCarryMarketSnapshot(
            venue="okx",
            base=base,
            quote=quote,
            spot_instrument_id=f"okx:{spot_id}:spot",
            perpetual_instrument_id=f"okx:{swap_id}:perpetual",
            spot_book=spot_book,
            perpetual_book=swap_book,
            mark_price=(swap_book.best_bid + swap_book.best_ask) / Decimal(2),
            last_funding_rate=Decimal(funding["fundingRate"]),
            next_funding_time=datetime.fromtimestamp(
                int(funding["nextFundingTime"]) / 1000,
                tz=UTC,
            ),
            funding_history=tuple(
                FundingObservation(
                    rate=Decimal(item.get("realizedRate") or item["fundingRate"]),
                    funding_time=datetime.fromtimestamp(
                        int(item["fundingTime"]) / 1000,
                        tz=UTC,
                    ),
                )
                for item in history
            ),
            observed_at=observed_at,
        )

    async def _get(
        self,
        client: httpx.AsyncClient,
        path: str,
        params: dict[str, str | int],
    ) -> dict[str, object]:
        response = await client.get(f"{self._base_url}{path}", params=params)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "0":
            raise RuntimeError(f"OKX API error: {payload.get('code')} {payload.get('msg')}")
        return payload

    @staticmethod
    def _data(payload: dict[str, object]) -> list[dict[str, str]]:
        data = payload.get("data")
        if not isinstance(data, list):
            raise TypeError("unexpected OKX response")
        return data

    @classmethod
    def _first_data(cls, payload: dict[str, object]) -> dict[str, str]:
        data = cls._data(payload)
        if not data:
            raise ValueError("OKX response contains no data")
        return data[0]

    @staticmethod
    def _parse_book(
        payload: dict[str, object],
        observed_at: datetime,
        quantity_multiplier: Decimal,
    ) -> OrderBook:
        raw_bids = payload.get("bids", [])
        raw_asks = payload.get("asks", [])
        if not isinstance(raw_bids, list) or not isinstance(raw_asks, list):
            raise TypeError("unexpected OKX order book response")

        bids = tuple(
            OrderBookLevel(
                price=Decimal(level[0]),
                quantity=Decimal(level[1]) * quantity_multiplier,
            )
            for level in raw_bids
        )
        asks = tuple(
            OrderBookLevel(
                price=Decimal(level[0]),
                quantity=Decimal(level[1]) * quantity_multiplier,
            )
            for level in raw_asks
        )
        return OrderBook(bids=bids, asks=asks, observed_at=observed_at)
