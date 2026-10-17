from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.backtest.cash_expiry_probe import evaluate_cash_expiry_probe

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "docs/historical-acquisition-plans/cash-independent-expiry-source-probes-v1.json"
CORPUS = ROOT / "tests/fixtures/historical"
SOURCE_BASE = "https://www.okx.com"


def pinned_cash_futures() -> set[str]:
    """Derive *actual* existing expiry identities rather than trusting a list."""
    index = json.loads((CORPUS / "corpus-index.json").read_text())
    futures = set()
    for entry in index["entries"]:
        if entry["strategy"] != "cash-and-carry":
            continue
        manifest = json.loads((CORPUS / entry["fixture_path"] / "manifest.json").read_text())
        if manifest["entry_market_date"] != entry["entry_market_date"]:
            raise ValueError("pinned Cash index and manifest date differ")
        futures.add(manifest["instrument"]["future_instrument_id"])
    return futures


def validated_candidates(registry: dict[str, Any], pinned: set[str]) -> list[dict[str, str]]:
    if not isinstance(registry, dict) or set(registry) != {
        "schema_version", "evidence_type", "study_id", "research_only",
        "outcome_blind", "known_pinned_futures_expiries", "candidates",
        "required_sources", "source_availability_status",
        "acquisition_approved", "promotion_approved",
    }:
        raise ValueError("Cash independent-expiry registry schema mismatch")
    if not (
        registry["schema_version"] == 1
        and registry["research_only"] is True
        and registry["outcome_blind"] is True
        and registry["acquisition_approved"] is False
        and registry["promotion_approved"] is False
        and registry["source_availability_status"] == "unverified"
        and sorted(registry["known_pinned_futures_expiries"]) == sorted(pinned)
    ):
        raise ValueError("Cash independent-expiry registry governance/pinned mismatch")
    targets = registry["candidates"]
    if not isinstance(targets, list) or len(targets) != 2:
        raise ValueError("requires two frozen Cash expiry candidates")
    ids = set()
    futures = set()
    used_dates = set()
    for target in targets:
        if not isinstance(target, dict) or set(target) != {
            "id", "future_id", "entry_market_date", "exit_market_date", "expiry_at",
        }:
            raise ValueError("invalid Cash candidate fields")
        contract = target["future_id"]
        expiry = datetime.fromisoformat(target["expiry_at"])
        if expiry.tzinfo is None:
            raise ValueError("Cash expiry must be timezone-aware")
        expiry = expiry.astimezone(UTC)
        entry, exit_day = (date.fromisoformat(target[k]) for k in (
            "entry_market_date", "exit_market_date"
        ))
        if not (
            contract == f"BTC-USDT-{expiry:%y%m%d}"
            and entry < exit_day < expiry.date()
            and expiry.hour == 8 and expiry.minute == 0
            and exit_day <= date(2026, 10, 17)
        ):
            raise ValueError("Cash candidate FUTURES identity or date ordering invalid")
        if (
            target["id"] in ids or contract in futures or contract in pinned
            or entry in used_dates or exit_day in used_dates
        ):
            raise ValueError("duplicate or already-pinned Cash expiry/date")
        ids.add(target["id"])
        futures.add(contract)
        used_dates.update((entry, exit_day))
    return targets


def spot_archive_catalog_status(
    client: httpx.Client, market_date: str,
) -> dict[str, Any]:
    date_at = datetime.combine(date.fromisoformat(market_date), datetime.min.time(), tzinfo=UTC)
    moment = str(int(date_at.timestamp() * 1000))
    query = OkxHistoricalCatalogQuery(
        module="4", instrument_type="SPOT",
        date_aggregation="daily", begin_ms=int(moment), end_ms=int(moment),
        instrument_ids=("BTC-USDT",),
    )
    response = client.get(SOURCE_BASE + OKX_HISTORY_ENDPOINT, params=query.params())
    response.raise_for_status()
    raw = response.json()
    if not isinstance(raw, dict) or raw.get("code") != "0":
        raise ValueError("official SPOT catalog response invalid")
    files = parse_okx_history_catalog(raw, query)
    matches = [
        f for f in files
        if f.instrument_id == "BTC-USDT" and f.data_date.date().isoformat() == market_date
    ]
    if len(matches) != 1:
        return {"status": "unavailable", "matching_archive_count": len(matches)}
    return {
        "status": "catalog_identity_only",
        "matching_archive_count": 1,
        "archive_filename": matches[0].filename,
        "download_sha256_verified": False,
        "l2_sample_verified": False,
    }


def source_discovery(day: str, dest: Path) -> dict[str, Any]:
    args = [
        sys.executable, str(ROOT / "scripts/discover_okx_cash_history.py"),
        day, "--output", str(dest), "--max-raw-mb", "512",
    ]
    try:
        run = subprocess.run(args, capture_output=True, text=True, timeout=600, check=False)
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "archive_discovery_timeout"}
    if run.returncode != 0 or not dest.is_file():
        return {"status": "error", "reason": f"archive_discovery_exit_{run.returncode}"}
    try:
        return json.loads(dest.read_text())
    except (ValueError, OSError):
        return {"status": "error", "reason": "invalid_discovery_report"}


def probe_candidate(
    target: dict[str, str], output: Path, client: httpx.Client,
) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "id": target["id"], "future_id": target["future_id"],
        "entry_market_date": target["entry_market_date"],
        "exit_market_date": target["exit_market_date"],
        "expiry_at": target["expiry_at"], "dates": {},
        "source_identity_verified": False,
        "complete_l2_sample_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }
    for name, day in (
        ("entry", target["entry_market_date"]),
        ("exit", target["exit_market_date"]),
    ):
        result = source_discovery(day, output / f"{name}-future-discovery.json")
        if result.get("status") == "error":
            future = {"status": "error", "reason": result["reason"]}
        else:
            try:
                checked = evaluate_cash_expiry_probe(
                    result, market_date=day, expected_future_id=target["future_id"]
                )
                future = checked.to_payload()
            except (ValueError, KeyError, TypeError) as error:
                future = {"status": "error", "reason": type(error).__name__}
        try:
            spot = spot_archive_catalog_status(client, day)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
            spot = {"status": "error", "reason": type(error).__name__}
        evidence["dates"][name] = {"future": future, "spot": spot}
    evidence["source_identity_verified"] = all(
        evidence["dates"][leg]["future"]["status"] == "identity_verified"
        and evidence["dates"][leg]["spot"]["status"] == "catalog_identity_only"
        for leg in ("entry", "exit")
    )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(REGISTRY.read_text())
    targets = validated_candidates(raw, pinned_cash_futures())
    matches = [x for x in targets if x["id"] == args.candidate_id]
    if len(matches) != 1:
        parser.error("candidate-id must identify a frozen unpinned expiry")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        evidence = probe_candidate(matches[0], args.output_dir, client)
    result = {
        "schema_version": 1,
        "evidence_type": "cash_independent_expiry_retrospective_source_feasibility",
        "study_id": raw["study_id"],
        "candidate": evidence,
        "source_catalog_ready": evidence["source_identity_verified"],
        "full_orderbook_source_readiness": "unassessed",
        "acquisition_approved": False,
        "promotion_approved": False,
        "note": "Catalog/chain identity only; no sampled L2 order books, contemporaneous publication or backtest outcomes verified.",
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
