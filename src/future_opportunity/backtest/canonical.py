from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from future_opportunity.backtest.model import (
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
    HistoricalOrderBookObservation,
)
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


CANONICAL_ORDER_BOOK_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class CanonicalReplaySummary:
    sha256: str
    sample_count: int
    observed_start: datetime
    observed_end: datetime


def write_canonical_order_books(
    observations: Iterable[HistoricalOrderBookObservation],
    destination: Path,
) -> CanonicalReplaySummary:
    """Write deterministic full-book JSONL and return its content evidence."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    count = 0
    observed_start: datetime | None = None
    observed_end: datetime | None = None

    with destination.open("wb") as output:
        for observation in observations:
            payload = _observation_payload(observation)
            encoded = (
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                )
                + "\n"
            ).encode("utf-8")
            output.write(encoded)
            digest.update(encoded)

            count += 1
            if observed_start is None:
                observed_start = observation.observed_at
            observed_end = observation.observed_at

    if count == 0 or observed_start is None or observed_end is None:
        raise ValueError("canonical replay requires at least one observation")

    return CanonicalReplaySummary(
        sha256=digest.hexdigest(),
        sample_count=count,
        observed_start=observed_start,
        observed_end=observed_end,
    )


def iter_canonical_order_books(
    source: Path,
) -> Iterator[HistoricalOrderBookObservation]:
    """Read deterministic canonical order-book JSONL with strict schema checks."""
    with source.open(encoding="utf-8") as input_file:
        previous_observed_at: datetime | None = None
        for line_number, raw_line in enumerate(input_file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid canonical JSON at line {line_number}"
                ) from error
            if not isinstance(payload, dict):
                raise TypeError(
                    f"canonical replay line {line_number} must be an object"
                )
            if payload.get("schema_version") != CANONICAL_ORDER_BOOK_SCHEMA_VERSION:
                raise ValueError(
                    f"unsupported canonical schema at line {line_number}"
                )

            observed_at = _parse_datetime(
                payload.get("observed_at"),
                line_number,
            )
            if (
                previous_observed_at is not None
                and observed_at < previous_observed_at
            ):
                raise ValueError(
                    "canonical replay timestamps must be non-decreasing "
                    f"(line {line_number})"
                )
            previous_observed_at = observed_at

            source_line = payload.get("source_line")
            if not isinstance(source_line, int) or source_line <= 0:
                raise ValueError(
                    f"invalid canonical source_line at line {line_number}"
                )

            instrument_id = payload.get("instrument_id")
            action = payload.get("source_action")
            if not isinstance(instrument_id, str) or not instrument_id:
                raise ValueError(
                    f"invalid canonical instrument_id at line {line_number}"
                )
            if action not in {"snapshot", "update"}:
                raise ValueError(
                    f"invalid canonical source_action at line {line_number}"
                )

            yield HistoricalOrderBookObservation(
                instrument_id=instrument_id,
                action=action,
                source_line=source_line,
                observed_at=observed_at,
                book=OrderBook(
                    bids=_parse_levels(
                        payload.get("bids"),
                        line_number=line_number,
                        reverse=True,
                    ),
                    asks=_parse_levels(
                        payload.get("asks"),
                        line_number=line_number,
                        reverse=False,
                    ),
                    observed_at=observed_at,
                ),
            )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _observation_payload(
    observation: HistoricalOrderBookObservation,
) -> dict[str, object]:
    if observation.observed_at.tzinfo is None:
        raise ValueError("canonical replay timestamps must be timezone-aware")
    observed_at = observation.observed_at.astimezone(UTC)
    return {
        "schema_version": CANONICAL_ORDER_BOOK_SCHEMA_VERSION,
        "instrument_id": observation.instrument_id,
        "source_action": observation.action,
        "source_line": observation.source_line,
        "observed_at": observed_at.isoformat(),
        "bids": [
            [str(level.price), str(level.quantity)]
            for level in observation.book.bids
        ],
        "asks": [
            [str(level.price), str(level.quantity)]
            for level in observation.book.asks
        ],
    }


def _parse_datetime(value: Any, line_number: int) -> datetime:
    if not isinstance(value, str):
        raise ValueError(
            f"invalid canonical observed_at at line {line_number}"
        )
    try:
        result = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"invalid canonical observed_at at line {line_number}"
        ) from error
    if result.tzinfo is None:
        raise ValueError(
            f"canonical observed_at must be timezone-aware at line {line_number}"
        )
    return result.astimezone(UTC)


def _parse_levels(
    value: Any,
    *,
    line_number: int,
    reverse: bool,
) -> tuple[OrderBookLevel, ...]:
    if not isinstance(value, list):
        raise TypeError(
            f"canonical levels must be a list at line {line_number}"
        )

    levels: list[OrderBookLevel] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(
                f"canonical level must be [price,quantity] at line {line_number}"
            )
        price = _decimal(item[0], "price", line_number)
        quantity = _decimal(item[1], "quantity", line_number)
        if price <= 0 or quantity <= 0:
            raise ValueError(
                f"canonical price/quantity must be positive at line {line_number}"
            )
        levels.append(OrderBookLevel(price=price, quantity=quantity))

    ordered = sorted(levels, key=lambda level: level.price, reverse=reverse)
    if levels != ordered:
        raise ValueError(
            f"canonical levels are not price-sorted at line {line_number}"
        )
    return tuple(levels)


def _decimal(value: Any, name: str, line_number: int) -> Decimal:
    if not isinstance(value, str):
        raise TypeError(
            f"canonical {name} must be a string at line {line_number}"
        )
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(
            f"invalid canonical {name} at line {line_number}"
        ) from error



CANONICAL_FUNDING_SCHEMA_VERSION = 1


def write_canonical_funding(
    observations: Iterable[HistoricalFundingObservation],
    destination: Path,
) -> CanonicalReplaySummary:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    count = 0
    observed_start: datetime | None = None
    observed_end: datetime | None = None

    with destination.open("wb") as output:
        for observation in observations:
            payload = {
                "schema_version": CANONICAL_FUNDING_SCHEMA_VERSION,
                "instrument_id": observation.instrument_id,
                "source_line": observation.source_line,
                "funding_time": observation.funding_time.astimezone(UTC).isoformat(),
                "funding_rate": str(observation.funding_rate),
            }
            encoded = (
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                )
                + "\n"
            ).encode("utf-8")
            output.write(encoded)
            digest.update(encoded)
            count += 1
            if observed_start is None:
                observed_start = observation.funding_time
            observed_end = observation.funding_time

    if count == 0 or observed_start is None or observed_end is None:
        raise ValueError("canonical funding replay requires at least one observation")

    return CanonicalReplaySummary(
        sha256=digest.hexdigest(),
        sample_count=count,
        observed_start=observed_start,
        observed_end=observed_end,
    )


def iter_canonical_funding(
    source: Path,
) -> Iterator[HistoricalFundingObservation]:
    previous_time: datetime | None = None
    with source.open(encoding="utf-8") as input_file:
        for line_number, raw_line in enumerate(input_file, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid canonical funding JSON at line {line_number}"
                ) from error
            if not isinstance(payload, dict):
                raise TypeError(
                    f"canonical funding line {line_number} must be an object"
                )
            if payload.get("schema_version") != CANONICAL_FUNDING_SCHEMA_VERSION:
                raise ValueError(
                    f"unsupported canonical funding schema at line {line_number}"
                )

            instrument_id = payload.get("instrument_id")
            source_line = payload.get("source_line")
            raw_time = payload.get("funding_time")
            raw_rate = payload.get("funding_rate")
            if not isinstance(instrument_id, str) or not instrument_id:
                raise ValueError(
                    f"invalid funding instrument_id at line {line_number}"
                )
            if not isinstance(source_line, int) or source_line <= 1:
                raise ValueError(
                    f"invalid funding source_line at line {line_number}"
                )
            funding_time = _parse_datetime(raw_time, line_number)
            rate = _decimal(raw_rate, "funding_rate", line_number)
            if previous_time is not None and funding_time <= previous_time:
                raise ValueError(
                    "canonical funding timestamps must be strictly increasing "
                    f"(line {line_number})"
                )
            previous_time = funding_time
            yield HistoricalFundingObservation(
                instrument_id=instrument_id,
                source_line=source_line,
                funding_time=funding_time,
                funding_rate=rate,
            )



CANONICAL_MARK_PRICE_SCHEMA_VERSION = 1


def write_canonical_mark_prices(
    candles: Iterable[HistoricalMarkPriceCandle],
    destination: Path,
) -> CanonicalReplaySummary:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    count = 0
    observed_start: datetime | None = None
    observed_end: datetime | None = None

    with destination.open("wb") as output:
        for candle in candles:
            payload = {
                "schema_version": CANONICAL_MARK_PRICE_SCHEMA_VERSION,
                "instrument_id": candle.instrument_id,
                "started_at": candle.started_at.astimezone(UTC).isoformat(),
                "open": str(candle.open_price),
                "high": str(candle.high_price),
                "low": str(candle.low_price),
                "close": str(candle.close_price),
                "confirmed": candle.confirmed,
            }
            encoded = (
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                )
                + "\n"
            ).encode("utf-8")
            output.write(encoded)
            digest.update(encoded)
            count += 1
            if observed_start is None:
                observed_start = candle.started_at
            observed_end = candle.started_at

    if count == 0 or observed_start is None or observed_end is None:
        raise ValueError("canonical mark-price replay requires at least one candle")

    return CanonicalReplaySummary(
        sha256=digest.hexdigest(),
        sample_count=count,
        observed_start=observed_start,
        observed_end=observed_end,
    )


def iter_canonical_mark_prices(
    source: Path,
) -> Iterator[HistoricalMarkPriceCandle]:
    previous_time: datetime | None = None
    with source.open(encoding="utf-8") as input_file:
        for line_number, raw_line in enumerate(input_file, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid canonical mark-price JSON at line {line_number}"
                ) from error
            if not isinstance(payload, dict):
                raise TypeError(
                    f"canonical mark-price line {line_number} must be an object"
                )
            if payload.get("schema_version") != CANONICAL_MARK_PRICE_SCHEMA_VERSION:
                raise ValueError(
                    f"unsupported canonical mark-price schema at line {line_number}"
                )
            instrument_id = payload.get("instrument_id")
            if not isinstance(instrument_id, str) or not instrument_id:
                raise ValueError(
                    f"invalid mark-price instrument_id at line {line_number}"
                )
            started_at = _parse_datetime(
                payload.get("started_at"),
                line_number,
            )
            if previous_time is not None and started_at <= previous_time:
                raise ValueError(
                    "canonical mark-price timestamps must be strictly increasing "
                    f"(line {line_number})"
                )
            previous_time = started_at
            confirmed = payload.get("confirmed")
            if not isinstance(confirmed, bool):
                raise TypeError(
                    f"mark-price confirmed must be bool at line {line_number}"
                )
            yield HistoricalMarkPriceCandle(
                instrument_id=instrument_id,
                started_at=started_at,
                open_price=_decimal(payload.get("open"), "open", line_number),
                high_price=_decimal(payload.get("high"), "high", line_number),
                low_price=_decimal(payload.get("low"), "low", line_number),
                close_price=_decimal(payload.get("close"), "close", line_number),
                confirmed=confirmed,
            )
