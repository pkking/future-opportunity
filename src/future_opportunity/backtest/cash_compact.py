from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from future_opportunity.backtest.canonical import (
    iter_canonical_order_books,
    sha256_file,
    write_canonical_order_books,
)
from future_opportunity.backtest.compact import compact_order_book_observation
from future_opportunity.domain.capital.model import allocate_isolated_hedge


_COMPONENTS = (
    "entry_spot",
    "entry_future",
    "exit_spot",
    "exit_future",
)


def derive_cash_compact_fixture(
    prepared_root: Path,
    output_root: Path,
    *,
    capital: Decimal = Decimal("10000"),
    reserve_ratio: Decimal = Decimal("0.10"),
    futures_leverage: Decimal = Decimal(1),
    quantity_margin: Decimal = Decimal("1.20"),
) -> dict[str, Any]:
    if quantity_margin < 1:
        raise ValueError("quantity_margin must be at least 1")

    manifest_path = prepared_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict):
        raise TypeError("prepared Cash manifest must be an object")
    if manifest.get("strategy") != "cash-and-carry":
        raise ValueError("prepared fixture is not cash-and-carry")

    normalized = manifest.get("normalized")
    if not isinstance(normalized, dict):
        raise ValueError("prepared Cash fixture is missing normalized evidence")

    observations = {}
    components: dict[str, dict[str, Any]] = {}
    for key in _COMPONENTS:
        component = normalized.get(key)
        if not isinstance(component, dict):
            raise ValueError(f"prepared Cash fixture is missing {key}")
        relative = component.get("path")
        expected_sha = component.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"prepared Cash {key} path is invalid")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise ValueError(f"prepared Cash {key} checksum is invalid")
        path = prepared_root / relative
        if sha256_file(path) != expected_sha:
            raise ValueError(f"prepared Cash {key} checksum mismatch")
        loaded = tuple(iter_canonical_order_books(path))
        if len(loaded) != 1:
            raise ValueError(f"prepared Cash {key} must contain one book")
        observations[key] = loaded[0]
        components[key] = component

    entry_spot = observations["entry_spot"]
    entry_future = observations["entry_future"]
    hedge_notional_ratio = (
        entry_future.book.best_bid / entry_spot.book.best_ask
    )
    allocation = allocate_isolated_hedge(
        capital,
        reserve_ratio,
        futures_leverage,
        hedge_notional_ratio,
    )
    target_base_quantity = (
        allocation.spot_notional / entry_spot.book.best_ask
    )
    preserve_base_quantity = target_base_quantity * quantity_margin

    output_root.mkdir(parents=True, exist_ok=True)
    compact_normalized: dict[str, dict[str, Any]] = {}
    for key in _COMPONENTS:
        compact, evidence = compact_order_book_observation(
            observations[key],
            preserve_base_quantity=preserve_base_quantity,
        )
        output_path = output_root / f"{key}.jsonl"
        summary = write_canonical_order_books((compact,), output_path)
        compact_normalized[key] = {
            "path": output_path.name,
            "sha256": summary.sha256,
            "source_line": compact.source_line,
            "observed_at": compact.observed_at.isoformat(),
            "sample_at": components[key].get("sample_at"),
            "age_ms": components[key].get("age_ms"),
            "best_bid": str(compact.book.best_bid),
            "best_ask": str(compact.book.best_ask),
            "derivation": {
                "parent_canonical_sha256": str(components[key]["sha256"]),
                "frozen_capital": str(capital),
                "quantity_margin": str(quantity_margin),
                "hedge_notional_ratio": str(hedge_notional_ratio),
                "target_base_quantity": str(target_base_quantity),
                "preserve_base_quantity": str(preserve_base_quantity),
                "parent_bid_levels": evidence.source_bid_levels,
                "parent_ask_levels": evidence.source_ask_levels,
                "compact_bid_levels": evidence.compact_bid_levels,
                "compact_ask_levels": evidence.compact_ask_levels,
                "retained_bid_quantity": str(evidence.retained_bid_quantity),
                "retained_ask_quantity": str(evidence.retained_ask_quantity),
                "rule": (
                    "retain minimum best-price-outward levels on both sides "
                    "covering the declared preserved base quantity"
                ),
            },
        }

    parent_dataset_id = manifest.get("dataset_id")
    if not isinstance(parent_dataset_id, str) or not parent_dataset_id:
        raise ValueError("prepared Cash dataset_id is invalid")
    entry_market_date = manifest.get("entry_market_date")
    if not isinstance(entry_market_date, str):
        raise ValueError("prepared Cash entry_market_date is invalid")

    compact_manifest = {
        "schema_version": 1,
        "strategy": "cash-and-carry",
        "close_mode": manifest.get("close_mode"),
        "dataset_id": f"{parent_dataset_id}-target-compact",
        "venue": manifest.get("venue"),
        "base": manifest.get("base"),
        "quote": manifest.get("quote"),
        "entry_market_date": entry_market_date,
        "pinning_status": "prepared_unpinned",
        "derived_from_artifact": None,
        "fixture_scope": {
            "capital": str(capital),
            "reserve_ratio": str(reserve_ratio),
            "futures_leverage": str(futures_leverage),
            "quantity_margin": str(quantity_margin),
            "hedge_notional_ratio": str(hedge_notional_ratio),
            "target_base_quantity": str(target_base_quantity),
            "preserve_base_quantity": str(preserve_base_quantity),
            "purpose": (
                "offline deterministic replay of the frozen reference-capital "
                "scenario; not full-book market-capacity reconstruction"
            ),
        },
        "parent_dataset": {
            "dataset_id": parent_dataset_id,
            "manifest_sha256": sha256_file(manifest_path),
        },
        "sample_times": manifest.get("sample_times"),
        "max_staleness_ms": manifest.get("max_staleness_ms"),
        "instrument": manifest.get("instrument"),
        "sources": manifest.get("sources"),
        "normalized": compact_normalized,
    }
    path = output_root / "manifest.json"
    path.write_text(
        json.dumps(compact_manifest, indent=2, sort_keys=True) + "\n"
    )
    return compact_manifest


def finalize_cash_compact_fixture(
    root: Path,
    *,
    workflow_run: str,
    artifact_id: str,
    artifact_digest: str,
) -> dict[str, Any]:
    if not workflow_run.isdigit():
        raise ValueError("workflow_run must be numeric")
    if not artifact_id.isdigit():
        raise ValueError("artifact_id must be numeric")
    digest = artifact_digest.removeprefix("sha256:")
    if len(digest) != 64:
        raise ValueError("artifact_digest must be SHA-256")

    path = root / "manifest.json"
    manifest = json.loads(path.read_text())
    if not isinstance(manifest, dict):
        raise TypeError("compact Cash manifest must be an object")
    if manifest.get("pinning_status") != "prepared_unpinned":
        raise ValueError("compact Cash fixture is not awaiting finalization")

    manifest["pinning_status"] = "commit_ready"
    manifest["derived_from_artifact"] = {
        "workflow_run": workflow_run,
        "artifact_id": artifact_id,
        "artifact_zip_sha256": digest,
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest
