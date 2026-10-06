import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from future_opportunity.backtest.canonical import (
    write_canonical_funding,
    write_canonical_mark_prices,
    write_canonical_order_books,
)
from future_opportunity.backtest.fixture import load_funding_history_fixture
from future_opportunity.backtest.funding_compact import (
    derive_funding_compact_fixture,
    finalize_funding_compact_fixture,
)
from future_opportunity.backtest.sampling import (
    HistoricalSamplingRequest,
    historical_sampling_payload,
    sample_historical_market_days,
)
from future_opportunity.backtest.selection_provenance import (
    historical_selection_provenance_payload,
    selection_provenance_from_sampling_evidence,
)
from future_opportunity.backtest.model import (
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
    HistoricalOrderBookObservation,
)
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


DAY = datetime(2026, 9, 2, tzinfo=UTC)


def book_observation(
    instrument_id: str,
    observed_at: datetime,
    source_line: int,
) -> HistoricalOrderBookObservation:
    return HistoricalOrderBookObservation(
        instrument_id=instrument_id,
        action="snapshot" if source_line == 1 else "update",
        source_line=source_line,
        observed_at=observed_at,
        book=OrderBook(
            bids=(
                OrderBookLevel(price=Decimal("100"), quantity=Decimal("60")),
                OrderBookLevel(price=Decimal("99"), quantity=Decimal("60")),
            ),
            asks=(
                OrderBookLevel(price=Decimal("101"), quantity=Decimal("60")),
                OrderBookLevel(price=Decimal("102"), quantity=Decimal("60")),
            ),
            observed_at=observed_at,
        ),
    )


def build_prepared(
    root: Path,
    *,
    with_selection_provenance: bool = False,
) -> None:
    spot_path = root / "btc-usdt-spot-books.jsonl"
    swap_path = root / "btc-usdt-swap-books.jsonl"
    funding_path = root / "btc-usdt-swap-funding.jsonl"
    mark_path = root / "btc-usdt-swap-mark-price.jsonl"

    entry = DAY
    exit_at = DAY + timedelta(hours=23, minutes=45)
    spot_summary = write_canonical_order_books(
        (
            book_observation("BTC-USDT", entry, 1),
            book_observation("BTC-USDT", exit_at, 2),
        ),
        spot_path,
    )
    swap_summary = write_canonical_order_books(
        (
            book_observation("BTC-USDT-SWAP", entry, 1),
            book_observation("BTC-USDT-SWAP", exit_at, 2),
        ),
        swap_path,
    )
    funding_summary = write_canonical_funding(
        tuple(
            HistoricalFundingObservation(
                instrument_id="BTC-USDT-SWAP",
                source_line=index + 2,
                funding_time=DAY + timedelta(hours=hour),
                funding_rate=Decimal("0.0001"),
            )
            for index, hour in enumerate((0, 8, 16))
        ),
        funding_path,
    )
    mark_summary = write_canonical_mark_prices(
        tuple(
            HistoricalMarkPriceCandle(
                instrument_id="BTC-USDT-SWAP",
                started_at=DAY + timedelta(hours=hour),
                open_price=Decimal(100),
                high_price=Decimal(101),
                low_price=Decimal(99),
                close_price=Decimal("100.5"),
                confirmed=True,
            )
            for hour in (0, 8, 16)
        ),
        mark_path,
    )

    manifest = {
        "schema_version": 1,
        "dataset_id": "okx-btc-usdt-funding-carry-2026-09-02-v1",
        "venue": "okx",
        "base": "BTC",
        "quote": "USDT",
        "history_date_utc": "2026-09-02",
        "cadence_seconds": 900,
        "max_staleness_seconds": 0,
        "sources": {"fixture": True},
        "instrument_metadata": {
            "instrument_id": "BTC-USDT-SWAP",
            "instrument_family": "BTC-USDT",
            "instrument_type": "SWAP",
            "contract_value": "0.01",
            "contract_multiplier": "1",
            "contract_value_currency": "BTC",
            "settlement_currency": "USDT",
        },
        "normalized": {
            "spot_books": {
                "path": spot_path.name,
                "sha256": spot_summary.sha256,
                "sample_count": spot_summary.sample_count,
                "observed_start": spot_summary.observed_start.isoformat(),
                "observed_end": spot_summary.observed_end.isoformat(),
            },
            "swap_books": {
                "path": swap_path.name,
                "sha256": swap_summary.sha256,
                "sample_count": swap_summary.sample_count,
                "observed_start": swap_summary.observed_start.isoformat(),
                "observed_end": swap_summary.observed_end.isoformat(),
            },
            "funding": {
                "path": funding_path.name,
                "sha256": funding_summary.sha256,
                "sample_count": funding_summary.sample_count,
                "observed_start": funding_summary.observed_start.isoformat(),
                "observed_end": funding_summary.observed_end.isoformat(),
            },
            "mark_price": {
                "path": mark_path.name,
                "sha256": mark_summary.sha256,
                "sample_count": mark_summary.sample_count,
                "observed_start": mark_summary.observed_start.isoformat(),
                "observed_end": mark_summary.observed_end.isoformat(),
            },
        },
        "alignment": {
            "requested_samples": 96,
            "emitted_samples": 2,
            "coverage_ratio": str(Decimal(2) / Decimal(96)),
            "missing_spot_samples": 0,
            "missing_hedge_samples": 0,
            "stale_spot_samples": 94,
            "stale_hedge_samples": 94,
        },
        "evidence_limits": {"funding_mark_price": "interval_bound"},
    }
    if with_selection_provenance:
        sampling = historical_sampling_payload(
            sample_historical_market_days(
                HistoricalSamplingRequest(
                    strategy="funding-carry",
                    start_date="2026-09-02",
                    end_date="2026-09-02",
                    sample_size=1,
                    seed="fixture-selection",
                )
            )
        )
        provenance = selection_provenance_from_sampling_evidence(
            sampling,
            source_workflow_run="123",
            artifact_name="sample-123",
            artifact_id="456",
            artifact_digest="a" * 64,
        )
        manifest["selection_provenance"] = (
            historical_selection_provenance_payload(provenance)
        )

    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


def test_funding_compact_derivation_is_commit_ready_after_finalization(
    tmp_path: Path,
) -> None:
    prepared = tmp_path / "prepared"
    compact = tmp_path / "compact"
    prepared.mkdir()
    build_prepared(prepared)

    draft = derive_funding_compact_fixture(prepared, compact)

    assert draft["strategy"] == "funding-carry"
    assert draft["entry_market_date"] == "2026-09-02"
    assert draft["pinning_status"] == "prepared_unpinned"
    scope = draft["fixture_scope"]
    assert Decimal(scope["preserve_base_quantity"]) > Decimal(
        scope["target_base_quantity"]
    )

    finalized = finalize_funding_compact_fixture(
        compact,
        workflow_run="12345",
        artifact_id="67890",
        artifact_digest="sha256:" + "a" * 64,
    )
    assert finalized["pinning_status"] == "commit_ready"
    assert finalized["derived_from_artifact"] == {
        "workflow_run": "12345",
        "artifact_id": "67890",
        "artifact_zip_sha256": "a" * 64,
    }

    loaded = load_funding_history_fixture(compact)
    assert loaded.dataset_id == (
        "okx-btc-usdt-funding-carry-2026-09-02-v1-target-compact"
    )
    assert loaded.alignment.emitted_samples == 2


def test_funding_compact_preserves_and_loader_validates_selection_provenance(
    tmp_path: Path,
) -> None:
    prepared = tmp_path / "prepared-selection"
    compact = tmp_path / "compact-selection"
    prepared.mkdir()
    build_prepared(prepared, with_selection_provenance=True)

    parent_manifest = json.loads((prepared / "manifest.json").read_text())
    draft = derive_funding_compact_fixture(prepared, compact)

    assert draft["selection_provenance"] == parent_manifest["selection_provenance"]

    finalize_funding_compact_fixture(
        compact,
        workflow_run="12345",
        artifact_id="67890",
        artifact_digest="b" * 64,
    )
    loaded = load_funding_history_fixture(compact)
    assert loaded.manifest["selection_provenance"] == (
        parent_manifest["selection_provenance"]
    )

    manifest_path = compact / "manifest.json"
    tampered = json.loads(manifest_path.read_text())
    tampered["history_date_utc"] = "2026-09-03"
    tampered["entry_market_date"] = "2026-09-03"
    manifest_path.write_text(json.dumps(tampered, indent=2) + "\n")

    import pytest

    with pytest.raises(ValueError, match="outside selection provenance"):
        load_funding_history_fixture(compact)
