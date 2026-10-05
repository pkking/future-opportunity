import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from future_opportunity.backtest.canonical import write_canonical_order_books
from future_opportunity.backtest.cash_compact import (
    derive_cash_compact_fixture,
    finalize_cash_compact_fixture,
)
from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.backtest.model import HistoricalOrderBookObservation
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


ENTRY = datetime(2026, 6, 2, 0, 15, tzinfo=UTC)
EXIT = datetime(2026, 6, 25, 0, 15, tzinfo=UTC)
EXPIRY = datetime(2026, 6, 26, 8, tzinfo=UTC)
FUTURE_ID = "BTC-USDT-260626"


def observation(
    instrument_id: str,
    observed_at: datetime,
    source_line: int,
    bid: str,
    ask: str,
) -> HistoricalOrderBookObservation:
    return HistoricalOrderBookObservation(
        instrument_id=instrument_id,
        action="update",
        source_line=source_line,
        observed_at=observed_at,
        book=OrderBook(
            bids=(
                OrderBookLevel(price=Decimal(bid), quantity=Decimal("0.05")),
                OrderBookLevel(
                    price=Decimal(bid) - Decimal("1"),
                    quantity=Decimal("0.05"),
                ),
            ),
            asks=(
                OrderBookLevel(price=Decimal(ask), quantity=Decimal("0.05")),
                OrderBookLevel(
                    price=Decimal(ask) + Decimal("1"),
                    quantity=Decimal("0.05"),
                ),
            ),
            observed_at=observed_at,
        ),
    )


def build_prepared(root: Path) -> None:
    source = {
        "entry_spot": observation("BTC-USDT", ENTRY, 10, "100", "101"),
        "entry_future": observation(FUTURE_ID, ENTRY, 20, "103", "104"),
        "exit_spot": observation("BTC-USDT", EXIT, 30, "90", "91"),
        "exit_future": observation(FUTURE_ID, EXIT, 40, "90.5", "91.5"),
    }
    normalized = {}
    for key, item in source.items():
        path = root / f"{key}.jsonl"
        summary = write_canonical_order_books((item,), path)
        normalized[key] = {
            "path": path.name,
            "sha256": summary.sha256,
            "source_line": item.source_line,
            "observed_at": item.observed_at.isoformat(),
            "sample_at": item.observed_at.isoformat(),
            "age_ms": 0,
            "best_bid": str(item.book.best_bid),
            "best_ask": str(item.book.best_ask),
        }

    manifest = {
        "schema_version": 1,
        "strategy": "cash-and-carry",
        "close_mode": "pre-expiry",
        "dataset_id": (
            "okx-btc-usdt-cash-and-carry-"
            "2026-06-02-BTC-USDT-260626-v1"
        ),
        "entry_market_date": "2026-06-02",
        "venue": "okx",
        "base": "BTC",
        "quote": "USDT",
        "sample_times": {
            "entry": ENTRY.isoformat(),
            "exit": EXIT.isoformat(),
        },
        "max_staleness_ms": 5000,
        "instrument": {
            "future_instrument_id": FUTURE_ID,
            "expiry": EXPIRY.isoformat(),
            "metadata_provenance": {
                "type": "official_product_spec",
                "contract_value": "0.01",
                "contract_multiplier": "1",
                "contract_value_currency": "BTC",
            },
        },
        "sources": {"fixture": True},
        "normalized": normalized,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


def test_cash_compact_derivation_is_commit_ready_after_finalization(
    tmp_path: Path,
) -> None:
    prepared = tmp_path / "prepared"
    compact = tmp_path / "compact"
    prepared.mkdir()
    build_prepared(prepared)

    draft = derive_cash_compact_fixture(prepared, compact)

    assert draft["strategy"] == "cash-and-carry"
    assert draft["entry_market_date"] == "2026-06-02"
    assert draft["pinning_status"] == "prepared_unpinned"
    scope = draft["fixture_scope"]
    assert Decimal(scope["preserve_base_quantity"]) > Decimal(
        scope["target_base_quantity"]
    )
    assert Decimal(scope["hedge_notional_ratio"]) > Decimal(1)

    finalized = finalize_cash_compact_fixture(
        compact,
        workflow_run="12345",
        artifact_id="67890",
        artifact_digest="sha256:" + "b" * 64,
    )
    assert finalized["pinning_status"] == "commit_ready"
    assert finalized["derived_from_artifact"] == {
        "workflow_run": "12345",
        "artifact_id": "67890",
        "artifact_zip_sha256": "b" * 64,
    }

    case = load_cash_and_carry_close_fixture(compact)
    assert case.entry.observed_at == ENTRY
    assert case.exit.observed_at == EXIT
    assert case.entry.future_instrument_id == f"okx:{FUTURE_ID}:future"
