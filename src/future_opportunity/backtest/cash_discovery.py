from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


_MEMBER_PATTERN = re.compile(
    r"^(?P<instrument>BTC-USDT-\d{6})-"
    r"L2orderbook-400lv-(?P<date>\d{4}-\d{2}-\d{2})\.data$"
)


@dataclass(frozen=True, slots=True)
class HistoricalFutureDeliveryEvidence:
    instrument_id: str
    delivered_at: datetime
    settlement_price: Decimal


def future_id_from_archive_member(
    member: str,
    *,
    expected_market_date: str,
) -> str:
    match = _MEMBER_PATTERN.fullmatch(member)
    if match is None:
        raise ValueError(
            f"unexpected BTC-USDT futures archive member: {member}"
        )
    if match.group("date") != expected_market_date:
        raise ValueError(
            "future archive member market date differs from requested date"
        )
    return match.group("instrument")



def future_ids_from_archive_members(
    members: tuple[str, ...] | list[str],
    *,
    expected_market_date: str,
) -> tuple[str, ...]:
    future_ids = tuple(
        sorted(
            {
                future_id_from_archive_member(
                    member,
                    expected_market_date=expected_market_date,
                )
                for member in members
            }
        )
    )
    if not future_ids:
        raise ValueError("future chain archive has no BTC-USDT data members")
    return future_ids


def find_delivery_evidence(
    payload: dict[str, Any],
    *,
    future_id: str,
) -> HistoricalFutureDeliveryEvidence | None:
    if payload.get("code") not in (None, "0"):
        raise ValueError(
            f"OKX delivery history error: "
            f"{payload.get('code')} {payload.get('msg')}"
        )
    data = payload.get("data")
    if not isinstance(data, list):
        raise TypeError("unexpected OKX delivery history response")

    matches: list[HistoricalFutureDeliveryEvidence] = []
    for group in data:
        if not isinstance(group, dict):
            continue
        raw_timestamp = group.get("ts")
        details = group.get("details")
        if not isinstance(raw_timestamp, str) or not raw_timestamp.isdigit():
            continue
        if not isinstance(details, list):
            continue

        for detail in details:
            if not isinstance(detail, dict):
                continue
            instrument_id = detail.get("instId") or detail.get("insId")
            if instrument_id != future_id:
                continue
            raw_price = detail.get("px") or detail.get("settlePx")
            if not isinstance(raw_price, str):
                raise ValueError(
                    f"delivery evidence for {future_id} has no settlement price"
                )
            try:
                price = Decimal(raw_price)
            except InvalidOperation as error:
                raise ValueError(
                    f"invalid delivery price for {future_id}"
                ) from error
            if price <= 0:
                raise ValueError(
                    f"delivery price for {future_id} must be positive"
                )
            matches.append(
                HistoricalFutureDeliveryEvidence(
                    instrument_id=future_id,
                    delivered_at=datetime.fromtimestamp(
                        int(raw_timestamp) / 1000,
                        tz=UTC,
                    ),
                    settlement_price=price,
                )
            )

    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(
            f"multiple delivery records found for historical future {future_id}"
        )
    return matches[0]
