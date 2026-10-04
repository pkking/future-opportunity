from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import httpx

from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


async def get_okx(
    client: httpx.AsyncClient,
    base_url: str,
    path: str,
    params: dict[str, str | int],
) -> dict[str, object]:
    response = await client.get(f"{base_url.rstrip('/')}{path}", params=params)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != "0":
        raise RuntimeError(f"OKX API error: {payload.get('code')} {payload.get('msg')}")
    return payload


def okx_data(payload: dict[str, object]) -> list[dict[str, str]]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise TypeError("unexpected OKX response")
    return data


def okx_first_data(payload: dict[str, object]) -> dict[str, str]:
    data = okx_data(payload)
    if not data:
        raise ValueError("OKX response contains no data")
    return data[0]


def parse_okx_book(
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
