import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.backtest.canonical import write_canonical_order_books
from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.backtest.model import HistoricalOrderBookObservation
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


ENTRY = datetime(2026, 6, 1, 0, 15, tzinfo=UTC)
EXIT = datetime(2026, 6, 25, 0, 15, tzinfo=UTC)
EXPIRY = datetime(2026, 6, 26, 8, 0, tzinfo=UTC)


def observation(
    instrument_id: str,
    observed_at: datetime,
    source_line: int,
) -> HistoricalOrderBookObservation:
    return HistoricalOrderBookObservation(
        instrument_id=instrument_id,
        action="update",
        source_line=source_line,
        observed_at=observed_at - timedelta(milliseconds=20),
        book=OrderBook(
            bids=(OrderBookLevel(price=Decimal(100), quantity=Decimal(10)),),
            asks=(OrderBookLevel(price=Decimal(101), quantity=Decimal(10)),),
            observed_at=observed_at - timedelta(milliseconds=20),
        ),
    )


def build_fixture(
    root: Path,
    *,
    future_id: str = "BTC-USDT-260626",
    expiry: datetime = EXPIRY,
) -> None:
    components = {
        "entry_spot": observation("BTC-USDT", ENTRY, 10),
        "entry_future": observation(future_id, ENTRY, 20),
        "exit_spot": observation("BTC-USDT", EXIT, 30),
        "exit_future": observation(future_id, EXIT, 40),
    }
    normalized = {}
    for key, item in components.items():
        path = root / f"{key}.jsonl"
        summary = write_canonical_order_books((item,), path)
        normalized[key] = {
            "path": path.name,
            "sha256": summary.sha256,
        }

    manifest = {
        "schema_version": 1,
        "strategy": "cash-and-carry",
        "close_mode": "pre-expiry",
        "dataset_id": "cash-fixture-v1",
        "sample_times": {
            "entry": ENTRY.isoformat(),
            "exit": EXIT.isoformat(),
        },
        "max_staleness_ms": 1000,
        "instrument": {
            "future_instrument_id": future_id,
            "expiry": expiry.isoformat(),
            "metadata_provenance": {
                "type": "official_product_spec",
                "contract_value": "0.01",
                "contract_multiplier": "1",
                "contract_value_currency": "BTC",
            },
        },
        "normalized": normalized,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


def test_cash_fixture_loads_verified_pre_expiry_case(tmp_path: Path) -> None:
    build_fixture(tmp_path)

    case = load_cash_and_carry_close_fixture(tmp_path)

    assert case.case_id == "cash-fixture-v1"
    assert case.entry.observed_at == ENTRY
    assert case.exit.observed_at == EXIT
    assert case.entry.expiry == EXPIRY
    assert case.entry.future_instrument_id == "okx:BTC-USDT-260626:future"
    assert "future-metadata:official-product-spec" in case.evidence_ids


def test_cash_fixture_rejects_unproven_expired_metadata(tmp_path: Path) -> None:
    build_fixture(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["instrument"]["metadata_provenance"]["type"] = "inferred"
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="product-spec provenance"):
        load_cash_and_carry_close_fixture(tmp_path)



def test_cash_fixture_accepts_another_explicit_btcusdt_expiry_future(
    tmp_path: Path,
) -> None:
    future_id = "BTC-USDT-260731"
    expiry = datetime(2026, 7, 31, 8, tzinfo=UTC)
    build_fixture(
        tmp_path,
        future_id=future_id,
        expiry=expiry,
    )

    case = load_cash_and_carry_close_fixture(tmp_path)

    assert case.entry.future_instrument_id == f"okx:{future_id}:future"
    assert case.entry.expiry == expiry
