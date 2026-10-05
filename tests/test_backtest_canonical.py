from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.backtest.canonical import (
    iter_canonical_funding,
    iter_canonical_mark_prices,
    iter_canonical_order_books,
    sha256_file,
    write_canonical_funding,
    write_canonical_mark_prices,
    write_canonical_order_books,
)
from future_opportunity.backtest.model import (
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
    HistoricalOrderBookObservation,
)
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


def observation(
    *,
    action: str,
    source_line: int,
    second: int,
) -> HistoricalOrderBookObservation:
    observed_at = datetime(2026, 1, 1, 0, 0, second, tzinfo=UTC)
    return HistoricalOrderBookObservation(
        instrument_id="BTC-USDT",
        action=action,
        source_line=source_line,
        observed_at=observed_at,
        book=OrderBook(
            bids=(
                OrderBookLevel(
                    price=Decimal("100"),
                    quantity=Decimal("1.5"),
                ),
            ),
            asks=(
                OrderBookLevel(
                    price=Decimal("101"),
                    quantity=Decimal("2.5"),
                ),
            ),
            observed_at=observed_at,
        ),
    )


def test_canonical_jsonl_round_trips_and_hashes_exact_bytes(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "books.jsonl"
    expected = (
        observation(action="snapshot", source_line=1, second=0),
        observation(action="update", source_line=2, second=1),
    )

    summary = write_canonical_order_books(expected, destination)
    actual = tuple(iter_canonical_order_books(destination))

    assert actual == expected
    assert summary.sample_count == 2
    assert summary.observed_start == expected[0].observed_at
    assert summary.observed_end == expected[-1].observed_at
    assert summary.sha256 == sha256_file(destination)


def test_canonical_output_is_deterministic(tmp_path: Path) -> None:
    observations = (
        observation(action="snapshot", source_line=1, second=0),
        observation(action="update", source_line=2, second=1),
    )
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"

    first_summary = write_canonical_order_books(observations, first)
    second_summary = write_canonical_order_books(observations, second)

    assert first.read_bytes() == second.read_bytes()
    assert first_summary.sha256 == second_summary.sha256


def test_canonical_writer_rejects_empty_dataset(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one observation"):
        write_canonical_order_books((), tmp_path / "empty.jsonl")


def test_canonical_reader_rejects_schema_drift(tmp_path: Path) -> None:
    source = tmp_path / "bad.jsonl"
    source.write_text(
        '{"schema_version":2,"instrument_id":"BTC-USDT"}\n'
    )

    with pytest.raises(ValueError, match="unsupported canonical schema"):
        tuple(iter_canonical_order_books(source))


def test_canonical_funding_round_trips_with_deterministic_checksum(
    tmp_path: Path,
) -> None:
    source = (
        HistoricalFundingObservation(
            instrument_id="BTC-USDT-SWAP",
            source_line=2,
            funding_time=datetime(2026, 9, 1, tzinfo=UTC),
            funding_rate=Decimal("0.0001"),
        ),
        HistoricalFundingObservation(
            instrument_id="BTC-USDT-SWAP",
            source_line=3,
            funding_time=datetime(2026, 9, 1, 8, tzinfo=UTC),
            funding_rate=Decimal("-0.00002"),
        ),
    )
    destination = tmp_path / "funding.jsonl"

    summary = write_canonical_funding(source, destination)

    assert tuple(iter_canonical_funding(destination)) == source
    assert summary.sample_count == 2
    assert summary.sha256 == sha256_file(destination)


def test_canonical_mark_price_round_trips_exact_interval_evidence(
    tmp_path: Path,
) -> None:
    candles = (
        HistoricalMarkPriceCandle(
            instrument_id="BTC-USDT-SWAP",
            started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
            open_price=Decimal(100_000),
            high_price=Decimal(101_000),
            low_price=Decimal(99_000),
            close_price=Decimal(100_500),
            confirmed=True,
        ),
    )
    destination = tmp_path / "mark.jsonl"

    summary = write_canonical_mark_prices(candles, destination)

    assert tuple(iter_canonical_mark_prices(destination)) == candles
    assert summary.sample_count == 1
    assert summary.sha256 == sha256_file(destination)
