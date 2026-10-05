from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from future_opportunity.backtest.alignment import align_order_books
from future_opportunity.backtest.canonical import (
    iter_canonical_order_books,
    sha256_file,
    write_canonical_order_books,
)
from future_opportunity.backtest.compact import compact_order_book_observation
from future_opportunity.domain.capital.model import allocate_isolated_hedge


def derive_funding_compact_fixture(
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
        raise TypeError("prepared Funding manifest must be an object")

    normalized = manifest.get("normalized")
    if not isinstance(normalized, dict):
        raise ValueError("prepared Funding manifest is missing normalized data")

    spot_component = _component(normalized, "spot_books")
    swap_component = _component(normalized, "swap_books")
    funding_component = _component(normalized, "funding")
    mark_component = _component(normalized, "mark_price")

    spot_path = prepared_root / spot_component["path"]
    swap_path = prepared_root / swap_component["path"]
    funding_path = prepared_root / funding_component["path"]
    mark_path = prepared_root / mark_component["path"]
    for key, path, component in (
        ("spot_books", spot_path, spot_component),
        ("swap_books", swap_path, swap_component),
        ("funding", funding_path, funding_component),
        ("mark_price", mark_path, mark_component),
    ):
        _assert_checksum(path, str(component["sha256"]), key)

    history_date = manifest.get("history_date_utc")
    cadence_seconds = manifest.get("cadence_seconds")
    max_staleness_seconds = manifest.get("max_staleness_seconds")
    if not isinstance(history_date, str):
        raise ValueError("prepared Funding history_date_utc is invalid")
    if not isinstance(cadence_seconds, int) or cadence_seconds <= 0:
        raise ValueError("prepared Funding cadence is invalid")
    if (
        not isinstance(max_staleness_seconds, int)
        or max_staleness_seconds < 0
    ):
        raise ValueError("prepared Funding max staleness is invalid")

    day = datetime.fromisoformat(history_date).replace(tzinfo=UTC)
    cadence = timedelta(seconds=cadence_seconds)
    sample_end = day + timedelta(days=1) - cadence
    parent_alignment = align_order_books(
        iter_canonical_order_books(spot_path),
        iter_canonical_order_books(swap_path),
        start=day,
        end=sample_end,
        cadence=cadence,
        max_staleness=timedelta(seconds=max_staleness_seconds),
    )
    if len(parent_alignment.samples) < 2:
        raise ValueError("prepared Funding day has fewer than two aligned books")

    entry = parent_alignment.samples[0]
    exit_sample = parent_alignment.samples[-1]
    allocation = allocate_isolated_hedge(
        capital,
        reserve_ratio,
        futures_leverage,
    )
    target_base_quantity = (
        allocation.spot_notional / entry.spot.book.best_ask
    )
    preserve_base_quantity = target_base_quantity * quantity_margin

    entry_spot, entry_spot_evidence = compact_order_book_observation(
        entry.spot,
        preserve_base_quantity=preserve_base_quantity,
    )
    exit_spot, exit_spot_evidence = compact_order_book_observation(
        exit_sample.spot,
        preserve_base_quantity=preserve_base_quantity,
    )
    entry_swap, entry_swap_evidence = compact_order_book_observation(
        entry.hedge,
        preserve_base_quantity=preserve_base_quantity,
    )
    exit_swap, exit_swap_evidence = compact_order_book_observation(
        exit_sample.hedge,
        preserve_base_quantity=preserve_base_quantity,
    )

    output_root.mkdir(parents=True, exist_ok=True)
    compact_spot_path = output_root / "btc-usdt-spot-books.jsonl"
    compact_swap_path = output_root / "btc-usdt-swap-books.jsonl"
    compact_funding_path = output_root / "btc-usdt-swap-funding.jsonl"
    compact_mark_path = output_root / "btc-usdt-swap-mark-price.jsonl"

    spot_summary = write_canonical_order_books(
        (entry_spot, exit_spot),
        compact_spot_path,
    )
    swap_summary = write_canonical_order_books(
        (entry_swap, exit_swap),
        compact_swap_path,
    )
    shutil.copy2(funding_path, compact_funding_path)
    shutil.copy2(mark_path, compact_mark_path)

    compact_alignment = align_order_books(
        iter_canonical_order_books(compact_spot_path),
        iter_canonical_order_books(compact_swap_path),
        start=day,
        end=sample_end,
        cadence=cadence,
        max_staleness=timedelta(seconds=max_staleness_seconds),
    )

    compact_manifest = {
        "schema_version": 1,
        "dataset_id": (
            f"okx-btc-usdt-funding-carry-{history_date}-v1-target-compact"
        ),
        "strategy": "funding-carry",
        "venue": manifest.get("venue"),
        "base": manifest.get("base"),
        "quote": manifest.get("quote"),
        "entry_market_date": history_date,
        "history_date_utc": history_date,
        "cadence_seconds": cadence_seconds,
        "max_staleness_seconds": max_staleness_seconds,
        "pinning_status": "prepared_unpinned",
        "derived_from_artifact": None,
        "fixture_scope": {
            "capital": str(capital),
            "reserve_ratio": str(reserve_ratio),
            "futures_leverage": str(futures_leverage),
            "quantity_margin": str(quantity_margin),
            "entry_sample": entry.sampled_at.isoformat(),
            "exit_sample": exit_sample.sampled_at.isoformat(),
            "target_base_quantity": str(target_base_quantity),
            "preserve_base_quantity": str(preserve_base_quantity),
            "purpose": (
                "offline deterministic replay of the frozen reference-capital "
                "one-day case; not full-day market-capacity reconstruction"
            ),
        },
        "parent_dataset": {
            "dataset_id": manifest.get("dataset_id"),
            "manifest_sha256": sha256_file(manifest_path),
        },
        "parent_alignment": _alignment_view(parent_alignment),
        "alignment": _alignment_view(compact_alignment),
        "instrument_metadata": manifest.get("instrument_metadata"),
        "normalized": {
            "spot_books": {
                "path": compact_spot_path.name,
                "sha256": spot_summary.sha256,
                "sample_count": spot_summary.sample_count,
                "observed_start": spot_summary.observed_start.isoformat(),
                "observed_end": spot_summary.observed_end.isoformat(),
                "derivation": _derivation_view(
                    parent_sha=str(spot_component["sha256"]),
                    capital=capital,
                    quantity_margin=quantity_margin,
                    preserve_base_quantity=preserve_base_quantity,
                    entry=entry_spot_evidence,
                    exit_evidence=exit_spot_evidence,
                    entry_source_line=entry.spot.source_line,
                    exit_source_line=exit_sample.spot.source_line,
                ),
            },
            "swap_books": {
                "path": compact_swap_path.name,
                "sha256": swap_summary.sha256,
                "sample_count": swap_summary.sample_count,
                "observed_start": swap_summary.observed_start.isoformat(),
                "observed_end": swap_summary.observed_end.isoformat(),
                "derivation": _derivation_view(
                    parent_sha=str(swap_component["sha256"]),
                    capital=capital,
                    quantity_margin=quantity_margin,
                    preserve_base_quantity=preserve_base_quantity,
                    entry=entry_swap_evidence,
                    exit_evidence=exit_swap_evidence,
                    entry_source_line=entry.hedge.source_line,
                    exit_source_line=exit_sample.hedge.source_line,
                ),
            },
            "funding": {
                **funding_component,
                "sha256": sha256_file(compact_funding_path),
            },
            "mark_price": {
                **mark_component,
                "sha256": sha256_file(compact_mark_path),
            },
        },
        "sources": manifest.get("sources"),
        "evidence_limits": manifest.get("evidence_limits"),
    }
    compact_manifest_path = output_root / "manifest.json"
    compact_manifest_path.write_text(
        json.dumps(compact_manifest, indent=2, sort_keys=True) + "\n"
    )
    return compact_manifest


def finalize_funding_compact_fixture(
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
        raise TypeError("compact Funding manifest must be an object")
    if manifest.get("pinning_status") != "prepared_unpinned":
        raise ValueError("compact Funding fixture is not awaiting finalization")

    manifest["pinning_status"] = "commit_ready"
    manifest["derived_from_artifact"] = {
        "workflow_run": workflow_run,
        "artifact_id": artifact_id,
        "artifact_zip_sha256": digest,
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def _component(
    normalized: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    value = normalized.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"prepared Funding manifest is missing {key}")
    if not isinstance(value.get("path"), str):
        raise ValueError(f"prepared Funding {key} path is invalid")
    if not isinstance(value.get("sha256"), str):
        raise ValueError(f"prepared Funding {key} SHA is invalid")
    return value


def _assert_checksum(path: Path, expected: str, key: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(
            f"prepared Funding {key} checksum mismatch: {actual} != {expected}"
        )


def _alignment_view(report) -> dict[str, object]:
    return {
        "requested_samples": report.requested_samples,
        "emitted_samples": report.emitted_samples,
        "coverage_ratio": str(report.coverage_ratio),
        "missing_spot_samples": report.missing_spot_samples,
        "missing_hedge_samples": report.missing_hedge_samples,
        "stale_spot_samples": report.stale_spot_samples,
        "stale_hedge_samples": report.stale_hedge_samples,
    }


def _derivation_view(
    *,
    parent_sha: str,
    capital: Decimal,
    quantity_margin: Decimal,
    preserve_base_quantity: Decimal,
    entry,
    exit_evidence,
    entry_source_line: int,
    exit_source_line: int,
) -> dict[str, object]:
    return {
        "parent_canonical_sha256": parent_sha,
        "frozen_capital": str(capital),
        "quantity_margin": str(quantity_margin),
        "preserve_base_quantity": str(preserve_base_quantity),
        "rule": (
            "retain entry/exit observations only and minimum best-price-outward "
            "levels on both sides covering the declared preserved base quantity"
        ),
        "observations": {
            "entry": {
                "source_line": entry_source_line,
                "source_levels": {
                    "bids": entry.source_bid_levels,
                    "asks": entry.source_ask_levels,
                },
                "compact_levels": {
                    "bids": entry.compact_bid_levels,
                    "asks": entry.compact_ask_levels,
                },
                "retained": {
                    "bids": str(entry.retained_bid_quantity),
                    "asks": str(entry.retained_ask_quantity),
                },
            },
            "exit": {
                "source_line": exit_source_line,
                "source_levels": {
                    "bids": exit_evidence.source_bid_levels,
                    "asks": exit_evidence.source_ask_levels,
                },
                "compact_levels": {
                    "bids": exit_evidence.compact_bid_levels,
                    "asks": exit_evidence.compact_ask_levels,
                },
                "retained": {
                    "bids": str(exit_evidence.retained_bid_quantity),
                    "asks": str(exit_evidence.retained_ask_quantity),
                },
            },
        },
    }
