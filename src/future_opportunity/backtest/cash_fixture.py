from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from future_opportunity.application.backtest.cash_and_carry import (
    HistoricalCashAndCarryCloseCase,
)
from future_opportunity.backtest.canonical import (
    iter_canonical_order_books,
    sha256_file,
)
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot


def load_cash_and_carry_close_fixture(
    root: Path,
) -> HistoricalCashAndCarryCloseCase:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict):
        raise TypeError("cash fixture manifest must be an object")
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported cash fixture schema")
    if manifest.get("strategy") != "cash-and-carry":
        raise ValueError("fixture is not cash-and-carry")
    if manifest.get("close_mode") != "pre-expiry":
        raise ValueError("cash fixture must use pre-expiry close")

    normalized = manifest.get("normalized")
    if not isinstance(normalized, dict):
        raise ValueError("cash fixture is missing normalized evidence")

    observations = {}
    for key in (
        "entry_spot",
        "entry_future",
        "exit_spot",
        "exit_future",
    ):
        component = normalized.get(key)
        if not isinstance(component, dict):
            raise ValueError(f"cash fixture is missing {key}")
        relative = component.get("path")
        expected_sha = component.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"cash fixture {key} path is invalid")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise ValueError(f"cash fixture {key} checksum is invalid")
        path = root / relative
        if sha256_file(path) != expected_sha:
            raise ValueError(f"cash fixture checksum mismatch for {key}")
        loaded = tuple(iter_canonical_order_books(path))
        if len(loaded) != 1:
            raise ValueError(f"cash fixture {key} must contain one book")
        observations[key] = loaded[0]

    sample_times = manifest.get("sample_times")
    if not isinstance(sample_times, dict):
        raise ValueError("cash fixture is missing sample_times")
    entry_at = _aware_datetime(sample_times.get("entry"))
    exit_at = _aware_datetime(sample_times.get("exit"))
    max_staleness_ms = manifest.get("max_staleness_ms")
    if not isinstance(max_staleness_ms, int) or max_staleness_ms < 0:
        raise ValueError("cash fixture max_staleness_ms is invalid")

    for key, sample_at in (
        ("entry_spot", entry_at),
        ("entry_future", entry_at),
        ("exit_spot", exit_at),
        ("exit_future", exit_at),
    ):
        observation = observations[key]
        if observation.observed_at > sample_at:
            raise ValueError(f"cash fixture {key} is after sample time")
        age_ms = int(
            (sample_at - observation.observed_at).total_seconds() * 1000
        )
        if age_ms > max_staleness_ms:
            raise ValueError(f"cash fixture {key} exceeds staleness bound")

    instrument = manifest.get("instrument")
    if not isinstance(instrument, dict):
        raise ValueError("cash fixture is missing instrument")
    raw_future_id = instrument.get("future_instrument_id")
    expiry = _aware_datetime(instrument.get("expiry"))
    if raw_future_id != "BTC-USDT-260626":
        raise ValueError("unexpected cash fixture future instrument")

    provenance = instrument.get("metadata_provenance")
    if not isinstance(provenance, dict):
        raise ValueError("cash fixture is missing metadata provenance")
    if provenance.get("type") != "official_product_spec":
        raise ValueError("expired future metadata must use product-spec provenance")
    if provenance.get("contract_value") != "0.01":
        raise ValueError("unexpected BTCUSDT expiry future contract value")
    if provenance.get("contract_multiplier") != "1":
        raise ValueError("unexpected BTCUSDT expiry future contract multiplier")
    if provenance.get("contract_value_currency") != "BTC":
        raise ValueError("unexpected expiry future contract value currency")

    entry_spot = observations["entry_spot"]
    entry_future = observations["entry_future"]
    exit_spot = observations["exit_spot"]
    exit_future = observations["exit_future"]
    if entry_spot.instrument_id != "BTC-USDT":
        raise ValueError("unexpected entry spot instrument")
    if exit_spot.instrument_id != "BTC-USDT":
        raise ValueError("unexpected exit spot instrument")
    if entry_future.instrument_id != raw_future_id:
        raise ValueError("unexpected entry future instrument")
    if exit_future.instrument_id != raw_future_id:
        raise ValueError("unexpected exit future instrument")

    canonical_spot = "okx:BTC-USDT:spot"
    canonical_future = f"okx:{raw_future_id}:future"
    entry = CashAndCarryMarketSnapshot(
        venue="okx",
        base="BTC",
        quote="USDT",
        spot_instrument_id=canonical_spot,
        future_instrument_id=canonical_future,
        spot_book=entry_spot.book,
        future_book=entry_future.book,
        expiry=expiry,
        observed_at=entry_at,
    )
    exit_snapshot = CashAndCarryMarketSnapshot(
        venue="okx",
        base="BTC",
        quote="USDT",
        spot_instrument_id=canonical_spot,
        future_instrument_id=canonical_future,
        spot_book=exit_spot.book,
        future_book=exit_future.book,
        expiry=expiry,
        observed_at=exit_at,
    )

    dataset_id = manifest.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("cash fixture dataset_id is invalid")
    return HistoricalCashAndCarryCloseCase(
        case_id=dataset_id,
        entry=entry,
        exit=exit_snapshot,
        evidence_ids=(
            dataset_id,
            f"entry-spot-line:{entry_spot.source_line}",
            f"entry-future-line:{entry_future.source_line}",
            f"exit-spot-line:{exit_spot.source_line}",
            f"exit-future-line:{exit_future.source_line}",
            "future-metadata:official-product-spec",
        ),
    )


def _aware_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("fixture timestamp must be a string")
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("fixture timestamp must be timezone-aware")
    return result
