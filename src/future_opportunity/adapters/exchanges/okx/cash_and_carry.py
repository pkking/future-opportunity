from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import httpx

from future_opportunity.adapters.exchanges.okx.common import (
    get_okx,
    okx_data,
    okx_first_data,
    parse_okx_book,
)
from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    DeliverySettlement,
    OrderBook,
)


class OkxCashAndCarryMarketData:
    """Read-only OKX spot + USDT-margined dated-futures adapter."""

    def __init__(
        self,
        base_url: str = "https://www.okx.com",
        timeout_seconds: float = 10.0,
        max_futures: int = 4,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_futures = max_futures

    async def snapshots(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[CashAndCarryMarketSnapshot, ...]:
        base = base.upper()
        quote = quote.upper()
        spot_id = f"{base}-{quote}"
        family = f"{base}-{quote}"
        now = datetime.now(UTC)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            instruments_raw, spot_book_raw = await asyncio.gather(
                get_okx(
                    client,
                    self._base_url,
                    "/api/v5/public/instruments",
                    {"instType": "FUTURES", "instFamily": family},
                ),
                get_okx(
                    client,
                    self._base_url,
                    "/api/v5/market/books",
                    {"instId": spot_id, "sz": 100},
                ),
            )

            instruments = self._eligible_futures(
                okx_data(instruments_raw),
                base=base,
                quote=quote,
                now=now,
            )[: self._max_futures]

            future_books = await asyncio.gather(
                *(
                    get_okx(
                        client,
                        self._base_url,
                        "/api/v5/market/books",
                        {"instId": instrument["instId"], "sz": 100},
                    )
                    for instrument in instruments
                )
            )

        observed_at = datetime.now(UTC)
        spot_book = parse_okx_book(
            okx_first_data(spot_book_raw),
            observed_at,
            quantity_multiplier=Decimal(1),
        )

        snapshots: list[CashAndCarryMarketSnapshot] = []
        for instrument, book_raw in zip(instruments, future_books, strict=True):
            contract_value = Decimal(instrument["ctVal"])
            future_book = parse_okx_book(
                okx_first_data(book_raw),
                observed_at,
                quantity_multiplier=contract_value,
            )
            snapshots.append(
                CashAndCarryMarketSnapshot(
                    venue="okx",
                    base=base,
                    quote=quote,
                    spot_instrument_id=f"okx:{spot_id}:spot",
                    future_instrument_id=f"okx:{instrument['instId']}:future",
                    spot_book=spot_book,
                    future_book=future_book,
                    expiry=datetime.fromtimestamp(
                        int(instrument["expTime"]) / 1000,
                        tz=UTC,
                    ),
                    observed_at=observed_at,
                )
            )

        return tuple(snapshots)

    async def spot_book(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[str, OrderBook]:
        base = base.upper()
        quote = quote.upper()
        spot_id = f"{base}-{quote}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            raw = await get_okx(
                client,
                self._base_url,
                "/api/v5/market/books",
                {"instId": spot_id, "sz": 100},
            )

        observed_at = datetime.now(UTC)
        return (
            f"okx:{spot_id}:spot",
            parse_okx_book(
                okx_first_data(raw),
                observed_at,
                quantity_multiplier=Decimal(1),
            ),
        )

    async def delivery_settlement(
        self,
        future_instrument_id: str,
        base: str,
        quote: str = "USDT",
    ) -> DeliverySettlement | None:
        base = base.upper()
        quote = quote.upper()
        family = f"{base}-{quote}"
        raw_instrument_id = self._raw_future_id(future_instrument_id)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            payload = await get_okx(
                client,
                self._base_url,
                "/api/v5/public/delivery-exercise-history",
                {"instType": "FUTURES", "instFamily": family},
            )

        return self._find_delivery_settlement(
            payload,
            canonical_instrument_id=future_instrument_id,
            raw_instrument_id=raw_instrument_id,
        )

    @staticmethod
    def _raw_future_id(future_instrument_id: str) -> str:
        prefix = "okx:"
        suffix = ":future"
        if not (
            future_instrument_id.startswith(prefix)
            and future_instrument_id.endswith(suffix)
        ):
            raise ValueError(
                f"unexpected OKX future instrument id: {future_instrument_id}"
            )
        return future_instrument_id[len(prefix) : -len(suffix)]

    @staticmethod
    def _find_delivery_settlement(
        payload: dict[str, object],
        *,
        canonical_instrument_id: str,
        raw_instrument_id: str,
    ) -> DeliverySettlement | None:
        data = payload.get("data")
        if not isinstance(data, list):
            raise TypeError("unexpected OKX delivery history response")

        for group in data:
            if not isinstance(group, dict):
                continue
            timestamp = group.get("ts")
            details = group.get("details")
            if not isinstance(timestamp, str) or not isinstance(details, list):
                continue

            for detail in details:
                if not isinstance(detail, dict):
                    continue
                instrument_id = detail.get("instId") or detail.get("insId")
                price = detail.get("px") or detail.get("settlePx")
                if instrument_id != raw_instrument_id or not isinstance(price, str):
                    continue

                return DeliverySettlement(
                    venue="okx",
                    future_instrument_id=canonical_instrument_id,
                    settlement_price=Decimal(price),
                    settled_at=datetime.fromtimestamp(
                        int(timestamp) / 1000,
                        tz=UTC,
                    ),
                )

        return None

    @staticmethod
    def _eligible_futures(
        instruments: list[dict[str, str]],
        base: str,
        quote: str,
        now: datetime,
    ) -> list[dict[str, str]]:
        now_ms = int(now.timestamp() * 1000)
        eligible = [
            instrument
            for instrument in instruments
            if instrument.get("state") == "live"
            and instrument.get("ctType") == "linear"
            and instrument.get("settleCcy") == quote
            and instrument.get("ctValCcy") == base
            and instrument.get("expTime")
            and int(instrument["expTime"]) > now_ms
        ]
        return sorted(eligible, key=lambda instrument: int(instrument["expTime"]))
