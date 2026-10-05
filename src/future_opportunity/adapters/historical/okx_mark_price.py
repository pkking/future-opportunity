from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from future_opportunity.backtest.model import HistoricalMarkPriceCandle


OKX_MARK_PRICE_HISTORY_ENDPOINT = "/api/v5/market/history-mark-price-candles"


@dataclass(frozen=True, slots=True)
class OkxHistoricalMarkPriceQuery:
    instrument_id: str
    start_ms: int
    end_ms: int
    bar: str = "1m"

    def __post_init__(self) -> None:
        if not self.instrument_id:
            raise ValueError("instrument_id is required")
        if self.end_ms < self.start_ms:
            raise ValueError("end_ms must not be before start_ms")
        if self.bar != "1m":
            raise ValueError(
                "historical funding evidence currently requires 1m mark candles"
            )


class OkxHistoricalMarkPriceClient:
    def __init__(
        self,
        base_url: str = "https://www.okx.com",
        timeout_seconds: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def candles(
        self,
        query: OkxHistoricalMarkPriceQuery,
    ) -> tuple[HistoricalMarkPriceCandle, ...]:
        cursor = query.end_ms + 60_000
        collected: dict[datetime, HistoricalMarkPriceCandle] = {}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for _ in range(10_000):
                response = await client.get(
                    f"{self._base_url}{OKX_MARK_PRICE_HISTORY_ENDPOINT}",
                    params={
                        "instId": query.instrument_id,
                        "bar": query.bar,
                        "after": str(cursor),
                        "limit": "100",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                page = parse_okx_mark_price_page(
                    payload,
                    instrument_id=query.instrument_id,
                )
                if not page:
                    break

                for candle in page:
                    timestamp_ms = int(candle.started_at.timestamp() * 1000)
                    if query.start_ms <= timestamp_ms <= query.end_ms:
                        collected[candle.started_at] = candle

                oldest_ms = min(
                    int(item.started_at.timestamp() * 1000)
                    for item in page
                )
                if oldest_ms <= query.start_ms:
                    break
                if oldest_ms >= cursor:
                    raise RuntimeError(
                        "OKX mark-price pagination did not move backward"
                    )
                cursor = oldest_ms

        return tuple(
            sorted(collected.values(), key=lambda item: item.started_at)
        )


def parse_okx_mark_price_page(
    payload: dict[str, Any],
    *,
    instrument_id: str,
) -> tuple[HistoricalMarkPriceCandle, ...]:
    if payload.get("code") != "0":
        raise ValueError(
            f"OKX mark-price history error: "
            f"{payload.get('code')} {payload.get('msg')}"
        )
    data = payload.get("data")
    if not isinstance(data, list):
        raise TypeError("unexpected OKX mark-price history response")

    result: list[HistoricalMarkPriceCandle] = []
    for index, row in enumerate(data):
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError(
                f"mark-price candle row {index} must contain 6 fields"
            )
        raw_ts, raw_open, raw_high, raw_low, raw_close, raw_confirm = row
        if not isinstance(raw_ts, str) or not raw_ts.isdigit():
            raise ValueError(f"invalid mark-price timestamp at row {index}")
        prices = [
            _decimal(value, index)
            for value in (raw_open, raw_high, raw_low, raw_close)
        ]
        if raw_confirm not in {"0", "1"}:
            raise ValueError(f"invalid mark-price confirm at row {index}")
        result.append(
            HistoricalMarkPriceCandle(
                instrument_id=instrument_id,
                started_at=datetime.fromtimestamp(
                    int(raw_ts) / 1000,
                    tz=UTC,
                ),
                open_price=prices[0],
                high_price=prices[1],
                low_price=prices[2],
                close_price=prices[3],
                confirmed=raw_confirm == "1",
            )
        )
    return tuple(result)


def _decimal(value: Any, row: int) -> Decimal:
    if not isinstance(value, str):
        raise TypeError(f"mark-price value must be a string at row {row}")
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"invalid mark-price decimal at row {row}") from error
