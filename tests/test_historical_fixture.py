import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.backtest.canonical import (
    write_canonical_funding,
    write_canonical_mark_prices,
    write_canonical_order_books,
)
from future_opportunity.backtest.fixture import (
    build_funding_case,
    load_funding_history_fixture,
)
from future_opportunity.backtest.model import (
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
    HistoricalOrderBookObservation,
)
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


DAY = datetime(2026, 9, 1, tzinfo=UTC)


def book_observation(
    instrument_id: str,
    minute: int,
    source_line: int,
) -> HistoricalOrderBookObservation:
    observed_at = DAY + timedelta(minutes=minute)
    return HistoricalOrderBookObservation(
        instrument_id=instrument_id,
        action="snapshot" if source_line == 1 else "update",
        source_line=source_line,
        observed_at=observed_at,
        book=OrderBook(
            bids=(OrderBookLevel(price=Decimal(100), quantity=Decimal(100)),),
            asks=(OrderBookLevel(price=Decimal("100.1"), quantity=Decimal(100)),),
            observed_at=observed_at,
        ),
    )


def build_fixture(root: Path) -> None:
    spot = root / "spot.jsonl"
    swap = root / "swap.jsonl"
    funding = root / "funding.jsonl"
    mark = root / "mark.jsonl"

    spot_summary = write_canonical_order_books(
        (
            book_observation("BTC-USDT", 0, 1),
            book_observation("BTC-USDT", 15, 2),
        ),
        spot,
    )
    swap_summary = write_canonical_order_books(
        (
            book_observation("BTC-USDT-SWAP", 0, 1),
            book_observation("BTC-USDT-SWAP", 15, 2),
        ),
        swap,
    )
    funding_summary = write_canonical_funding(
        (
            HistoricalFundingObservation(
                instrument_id="BTC-USDT-SWAP",
                source_line=2,
                funding_time=DAY,
                funding_rate=Decimal("0.001"),
            ),
        ),
        funding,
    )
    mark_summary = write_canonical_mark_prices(
        (
            HistoricalMarkPriceCandle(
                instrument_id="BTC-USDT-SWAP",
                started_at=DAY,
                open_price=Decimal(100),
                high_price=Decimal(101),
                low_price=Decimal(99),
                close_price=Decimal(100),
                confirmed=True,
            ),
        ),
        mark,
    )
    manifest = {
        "schema_version": 1,
        "dataset_id": "fixture-v1",
        "venue": "okx",
        "history_date_utc": "2026-09-01",
        "cadence_seconds": 900,
        "max_staleness_seconds": 0,
        "alignment": {
            "requested_samples": 96,
            "emitted_samples": 2,
            "coverage_ratio": str(Decimal(2) / Decimal(96)),
        },
        "normalized": {
            "spot_books": {
                "path": spot.name,
                "sha256": spot_summary.sha256,
            },
            "swap_books": {
                "path": swap.name,
                "sha256": swap_summary.sha256,
            },
            "funding": {
                "path": funding.name,
                "sha256": funding_summary.sha256,
            },
            "mark_price": {
                "path": mark.name,
                "sha256": mark_summary.sha256,
            },
        },
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


def test_fixture_loader_verifies_checksums_and_alignment(tmp_path: Path) -> None:
    build_fixture(tmp_path)

    fixture = load_funding_history_fixture(tmp_path)

    assert fixture.dataset_id == "fixture-v1"
    assert fixture.alignment.emitted_samples == 2
    assert len(fixture.funding) == 1
    assert len(fixture.mark_prices) == 1

    case = build_funding_case(
        fixture,
        entry_index=0,
        exit_index=1,
    )
    assert case.entry.observed_at == DAY
    assert case.exit.observed_at == DAY + timedelta(minutes=15)


def test_fixture_loader_rejects_checksum_drift(tmp_path: Path) -> None:
    build_fixture(tmp_path)
    spot = tmp_path / "spot.jsonl"
    spot.write_text(spot.read_text() + "{}\n")

    with pytest.raises(ValueError, match="checksum mismatch"):
        load_funding_history_fixture(tmp_path)
