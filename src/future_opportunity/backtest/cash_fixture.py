from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
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
from future_opportunity.backtest.selection_provenance import (
    validate_selection_provenance_for_market_date,
)


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

    entry_market_date = manifest.get("entry_market_date")
    if not isinstance(entry_market_date, str):
        raise ValueError("cash fixture entry_market_date is invalid")
    selection_provenance = manifest.get("selection_provenance")
    if selection_provenance is not None:
        validate_selection_provenance_for_market_date(
            selection_provenance,
            strategy="cash-and-carry",
            market_date=entry_market_date,
        )

    normalized = manifest.get("normalized")
    if not isinstance(normalized, dict):
        raise ValueError("cash fixture is missing normalized evidence")
    _validate_derived_fixture(manifest, normalized)

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
    if (
        not isinstance(raw_future_id, str)
        or not raw_future_id.startswith("BTC-USDT-")
    ):
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



def _validate_derived_fixture(
    manifest: dict[str, Any],
    normalized: dict[str, Any],
) -> None:
    derived = manifest.get("derived_from_artifact")
    scope = manifest.get("fixture_scope")
    if derived is None and scope is None:
        return
    if manifest.get("pinning_status") != "commit_ready":
        raise ValueError(
            "derived cash fixture must be finalized as commit_ready"
        )
    if not isinstance(derived, dict) or not isinstance(scope, dict):
        raise ValueError(
            "derived cash fixture requires artifact and scope provenance"
        )

    artifact_sha = derived.get("artifact_zip_sha256")
    if not isinstance(artifact_sha, str) or len(artifact_sha) != 64:
        raise ValueError("derived cash fixture artifact checksum is invalid")
    if not str(derived.get("workflow_run", "")).isdigit():
        raise ValueError("derived cash fixture workflow run is invalid")
    if not str(derived.get("artifact_id", "")).isdigit():
        raise ValueError("derived cash fixture artifact id is invalid")

    capital = scope.get("capital")
    if capital != "10000":
        raise ValueError("derived cash fixture frozen capital is unsupported")
    if scope.get("quantity_margin") != "1.20":
        raise ValueError("derived cash fixture quantity margin is unsupported")

    for key in (
        "entry_spot",
        "entry_future",
        "exit_spot",
        "exit_future",
    ):
        component = normalized.get(key)
        if not isinstance(component, dict):
            raise ValueError(f"derived cash fixture is missing {key}")
        derivation = component.get("derivation")
        if not isinstance(derivation, dict):
            raise ValueError(
                f"derived cash fixture {key} is missing derivation evidence"
            )
        parent_sha = derivation.get("parent_canonical_sha256")
        if not isinstance(parent_sha, str) or len(parent_sha) != 64:
            raise ValueError(
                f"derived cash fixture {key} parent checksum is invalid"
            )
        if derivation.get("frozen_capital") != capital:
            raise ValueError(
                f"derived cash fixture {key} capital provenance drifted"
            )
        preserve = _decimal_field(
            derivation.get("preserve_base_quantity"),
            f"{key} preserve_base_quantity",
        )
        retained_ask = _decimal_field(
            derivation.get("retained_ask_quantity"),
            f"{key} retained_ask_quantity",
        )
        retained_bid = _decimal_field(
            derivation.get("retained_bid_quantity"),
            f"{key} retained_bid_quantity",
        )
        if preserve <= 0:
            raise ValueError(
                f"derived cash fixture {key} preserve quantity must be positive"
            )
        if retained_ask < preserve or retained_bid < preserve:
            raise ValueError(
                f"derived cash fixture {key} does not preserve target quantity"
            )


def _decimal_field(value: Any, name: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"derived cash fixture {name} must be a string")
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(
            f"derived cash fixture {name} is not decimal"
        ) from error
