from __future__ import annotations

import io
import json
import tarfile
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from future_opportunity.backtest.model import (
    HistoricalInstrumentMetadata,
    HistoricalOrderBookObservation,
)
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


_SUPPORTED_INSTRUMENT_TYPES = {"SPOT", "SWAP", "FUTURES"}


def iter_okx_l2_archive(
    path: Path,
    *,
    instrument_type: str,
    expected_instrument_id: str,
    metadata: HistoricalInstrumentMetadata | None = None,
) -> Iterator[HistoricalOrderBookObservation]:
    """Stream an official OKX module-4 tar.gz archive into canonical books."""
    if not path.is_file():
        raise FileNotFoundError(path)

    try:
        archive = tarfile.open(path, mode="r:gz")
    except tarfile.TarError as error:
        raise ValueError(f"unsupported OKX L2 archive: {path}") from error

    with archive:
        members = [
            item
            for item in archive.getmembers()
            if item.isfile() and item.name.endswith(".data")
        ]
        if len(members) != 1:
            raise ValueError(
                "OKX L2 archive must contain exactly one .data member"
            )

        source = archive.extractfile(members[0])
        if source is None:
            raise ValueError("unable to open OKX L2 archive member")

        with source, io.TextIOWrapper(source, encoding="utf-8-sig") as text:
            yield from iter_okx_l2_jsonl(
                text,
                instrument_type=instrument_type,
                expected_instrument_id=expected_instrument_id,
                metadata=metadata,
            )


def iter_okx_l2_jsonl(
    lines: Iterable[str],
    *,
    instrument_type: str,
    expected_instrument_id: str,
    metadata: HistoricalInstrumentMetadata | None = None,
) -> Iterator[HistoricalOrderBookObservation]:
    """Replay verified OKX snapshot/update JSONL with fail-closed normalization."""
    instrument_type = instrument_type.upper()
    if instrument_type not in _SUPPORTED_INSTRUMENT_TYPES:
        raise ValueError(
            f"unsupported OKX L2 instrument type: {instrument_type}"
        )
    if not expected_instrument_id:
        raise ValueError("expected_instrument_id is required")

    quantity_multiplier = _quantity_multiplier(
        instrument_type=instrument_type,
        expected_instrument_id=expected_instrument_id,
        metadata=metadata,
    )

    bids: dict[Decimal, Decimal] = {}
    asks: dict[Decimal, Decimal] = {}
    initialized = False
    previous_observed_at: datetime | None = None

    for source_line, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        event = _parse_event(line, source_line)
        instrument_id = _required_string(event, "instId", source_line)
        if instrument_id != expected_instrument_id:
            raise ValueError(
                "historical event instrument mismatch at line "
                f"{source_line}: {instrument_id} != {expected_instrument_id}"
            )

        action = _required_string(event, "action", source_line)
        if action not in {"snapshot", "update"}:
            raise ValueError(
                f"unsupported historical action at line {source_line}: {action}"
            )
        if not initialized and action != "snapshot":
            raise ValueError(
                "historical replay must begin with a snapshot "
                f"(line {source_line})"
            )

        observed_at = _timestamp(event, source_line)
        if previous_observed_at is not None and observed_at < previous_observed_at:
            raise ValueError(
                "historical timestamps must be non-decreasing "
                f"(line {source_line})"
            )

        raw_bids = _levels(event, "bids", source_line)
        raw_asks = _levels(event, "asks", source_line)

        if action == "snapshot":
            bids = {}
            asks = {}
            _apply_levels(
                bids,
                raw_bids,
                quantity_multiplier=quantity_multiplier,
                source_line=source_line,
            )
            _apply_levels(
                asks,
                raw_asks,
                quantity_multiplier=quantity_multiplier,
                source_line=source_line,
            )
            initialized = True
        else:
            _apply_levels(
                bids,
                raw_bids,
                quantity_multiplier=quantity_multiplier,
                source_line=source_line,
            )
            _apply_levels(
                asks,
                raw_asks,
                quantity_multiplier=quantity_multiplier,
                source_line=source_line,
            )

        previous_observed_at = observed_at
        yield HistoricalOrderBookObservation(
            instrument_id=instrument_id,
            action=action,
            source_line=source_line,
            observed_at=observed_at,
            book=OrderBook(
                bids=tuple(
                    OrderBookLevel(price=price, quantity=quantity)
                    for price, quantity in sorted(
                        bids.items(),
                        key=lambda item: item[0],
                        reverse=True,
                    )
                ),
                asks=tuple(
                    OrderBookLevel(price=price, quantity=quantity)
                    for price, quantity in sorted(asks.items())
                ),
                observed_at=observed_at,
            ),
        )


def _quantity_multiplier(
    *,
    instrument_type: str,
    expected_instrument_id: str,
    metadata: HistoricalInstrumentMetadata | None,
) -> Decimal:
    if instrument_type == "SPOT":
        return Decimal(1)

    if metadata is None:
        raise ValueError(
            "derivative historical replay requires pinned instrument metadata"
        )
    if metadata.instrument_id != expected_instrument_id:
        raise ValueError(
            "historical metadata instrument does not match replay instrument"
        )
    if metadata.instrument_type != instrument_type:
        raise ValueError(
            "historical metadata instrument type does not match replay type"
        )
    if metadata.contract_value is None or metadata.contract_multiplier is None:
        raise ValueError(
            "derivative metadata requires contract_value and contract_multiplier"
        )
    if metadata.contract_value <= 0 or metadata.contract_multiplier <= 0:
        raise ValueError(
            "derivative contract value and multiplier must be positive"
        )

    family = metadata.instrument_family or expected_instrument_id
    base_asset = family.split("-", maxsplit=1)[0].upper()
    contract_currency = (metadata.contract_value_currency or "").upper()
    if contract_currency != base_asset:
        raise ValueError(
            "derivative contract value currency is not the base asset; "
            "price-dependent normalization is unassessed"
        )

    return metadata.contract_value * metadata.contract_multiplier


def _parse_event(line: str, source_line: int) -> dict[str, Any]:
    try:
        value = json.loads(line)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid historical JSON at line {source_line}"
        ) from error
    if not isinstance(value, dict):
        raise TypeError(
            f"historical event must be an object at line {source_line}"
        )
    return value


def _required_string(
    event: dict[str, Any],
    key: str,
    source_line: int,
) -> str:
    value = event.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"historical event is missing {key} at line {source_line}"
        )
    return value


def _timestamp(event: dict[str, Any], source_line: int) -> datetime:
    raw = event.get("ts")
    if not isinstance(raw, str) or not raw.isdigit():
        raise ValueError(
            f"historical event has invalid ts at line {source_line}"
        )
    return datetime.fromtimestamp(int(raw) / 1000, tz=UTC)


def _levels(
    event: dict[str, Any],
    side: str,
    source_line: int,
) -> list[list[Any]]:
    value = event.get(side)
    if not isinstance(value, list):
        raise TypeError(
            f"historical event has invalid {side} at line {source_line}"
        )
    result: list[list[Any]] = []
    for level in value:
        if not isinstance(level, list) or len(level) != 3:
            raise ValueError(
                f"historical {side} level must contain "
                f"[price,size,orderCount] at line {source_line}"
            )
        result.append(level)
    return result


def _apply_levels(
    state: dict[Decimal, Decimal],
    levels: list[list[Any]],
    *,
    quantity_multiplier: Decimal,
    source_line: int,
) -> None:
    for level in levels:
        price = _positive_decimal(level[0], "price", source_line)
        size = _non_negative_decimal(level[1], "size", source_line)
        _non_negative_integer(level[2], "orderCount", source_line)

        quantity = size * quantity_multiplier
        if quantity == 0:
            state.pop(price, None)
        else:
            state[price] = quantity


def _positive_decimal(
    value: Any,
    name: str,
    source_line: int,
) -> Decimal:
    result = _decimal(value, name, source_line)
    if result <= 0:
        raise ValueError(
            f"historical {name} must be positive at line {source_line}"
        )
    return result


def _non_negative_decimal(
    value: Any,
    name: str,
    source_line: int,
) -> Decimal:
    result = _decimal(value, name, source_line)
    if result < 0:
        raise ValueError(
            f"historical {name} must be non-negative at line {source_line}"
        )
    return result


def _decimal(value: Any, name: str, source_line: int) -> Decimal:
    if not isinstance(value, str):
        raise TypeError(
            f"historical {name} must be a string at line {source_line}"
        )
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(
            f"historical {name} is not decimal at line {source_line}"
        ) from error


def _non_negative_integer(
    value: Any,
    name: str,
    source_line: int,
) -> int:
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError(
            f"historical {name} must be a non-negative integer string "
            f"at line {source_line}"
        )
    return int(value)
