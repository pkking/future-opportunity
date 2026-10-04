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
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot


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
            and instrument.get("settleCcy") == quote
            and instrument.get("ctValCcy") == base
            and instrument.get("expTime")
            and int(instrument["expTime"]) > now_ms
        ]
        return sorted(eligible, key=lambda instrument: int(instrument["expTime"]))
