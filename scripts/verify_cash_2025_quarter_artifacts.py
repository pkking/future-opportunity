#!/usr/bin/env python3
"""Fail-closed metadata audit for a frozen Cash 2025 quarter preparation run.

Presence of Actions artifacts is NOT verification of archive contents or PnL.
The separate historical campaign planner must inspect preparation evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


FROZEN_WAVES = {
    "q3": (
        "cash-2025-q3-12day-wave-001",
        "BTC-USDT-250926",
        "2025-09-25T00:15:00+00:00",
        "2025-09-26T08:00:00+00:00",
    ),
    "q4": (
        "cash-2025-q4-12day-wave-001",
        "BTC-USDT-251226",
        "2025-12-25T00:15:00+00:00",
        "2025-12-26T08:00:00+00:00",
    ),
}
SOURCE_RUN = "37755705789"
SOURCE_ARTIFACT = "11539833591"
SOURCE_DIGEST = (
    "sha256:f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74"
)
CASH_PREFIX = "okx-btc-cash-and-carry-"
KINDS = ("prepared", "compact", "actuals")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
UTC_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def _expected(manifest: Any, wave: str, run_id: str) -> dict[str, tuple[str, str]]:
    if wave not in FROZEN_WAVES:
        raise ValueError(f"unknown frozen wave: {wave}")
    if not isinstance(run_id, str) or not re.fullmatch(r"[1-9][0-9]*", run_id):
        raise ValueError("run_id must be a positive decimal integer")
    acquisition_id, future, exit_at, expiry_at = FROZEN_WAVES[wave]
    if not isinstance(manifest, dict):
        raise ValueError("acquisition manifest must be an object")
    if manifest.get("acquisition_id") != acquisition_id or manifest.get("funding") is not None:
        raise ValueError("manifest is not the frozen Cash-only acquisition")
    provenance = manifest.get("selection_provenance")
    if not isinstance(provenance, dict) or not isinstance(provenance.get("cash"), dict):
        raise ValueError("missing Cash selection provenance")
    selection = provenance["cash"]
    source = selection.get("source")
    if (
        selection.get("selection_kind") != "pre_registered_availability_sample"
        or selection.get("strategy") != "cash-and-carry"
        or not isinstance(source, dict)
        or str(source.get("workflow_run")) != SOURCE_RUN
        or str(source.get("artifact_id")) != SOURCE_ARTIFACT
        or source.get("artifact_digest") != SOURCE_DIGEST
    ):
        raise ValueError("Cash selection provenance does not match frozen source")
    cases = manifest.get("cash_cases")
    if not isinstance(cases, list) or len(cases) != 12:
        raise ValueError("frozen Cash wave must contain exactly 12 cases")

    expected: dict[str, tuple[str, str]] = {}
    dates: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Cash case must be an object")
        entry_at = case.get("entry_at")
        if not isinstance(entry_at, str) or not entry_at.endswith("T00:15:00+00:00"):
            raise ValueError("Cash entry must be at frozen 00:15 UTC")
        market_date = entry_at[:10]
        if not UTC_DATE.fullmatch(market_date):
            raise ValueError("invalid Cash entry date")
        if (
            case.get("future_id") != future
            or case.get("exit_at") != exit_at
            or case.get("expiry_at") != expiry_at
        ):
            raise ValueError(f"frozen contract/exit/expiry mismatch on {market_date}")
        if market_date in dates:
            raise ValueError(f"duplicate frozen Cash entry date: {market_date}")
        dates.append(market_date)
        suffix = f"{market_date}-{future}-{run_id}"
        expected[f"{CASH_PREFIX}{suffix}"] = (market_date, "prepared")
        expected[f"{CASH_PREFIX}compact-{suffix}"] = (market_date, "compact")
        expected[f"{CASH_PREFIX}actuals-{suffix}"] = (market_date, "actuals")
    sampling = selection.get("sampling")
    if (
        not isinstance(sampling, dict)
        or sampling.get("selected_market_dates") != dates
        or sampling.get("requested_sample_size") != 12
    ):
        raise ValueError("Cash case dates diverge from frozen source selection")
    return expected


def verify_inventory(
    manifest: Any, listing: Any, *, wave: str, run_id: str,
    acquisition_result: str = "success",
) -> dict[str, Any]:
    """Audit a single run inventory. Every error is included in the report."""
    report: dict[str, Any] = {
        "schema_version": 1,
        "evidence_type": "cash_2025_quarter_preparation_boundary",
        "wave": wave,
        "workflow_run": run_id,
        "acquisition_result": acquisition_result,
        "status": "failed",
        "expected_cash_count": 12,
        "expected_artifact_count_by_kind": {kind: 12 for kind in KINDS},
        "verified_artifact_count_by_kind": {kind: 0 for kind in KINDS},
        "artifacts_by_market_date": {},
        "missing_artifact_names": [],
        "unexpected_artifact_names": [],
        "errors": [],
        "artifact_digest_validation": "presence_and_format_only",
        "artifact_contents_verified": False,
        "l2_completeness_verified": False,
        "actuals_contents_verified": False,
        "corpus_mutation": False,
        "promotion_dispatched": False,
    }
    errors = report["errors"]
    if acquisition_result != "success":
        errors.append(f"acquisition job result is {acquisition_result!r}, not success")
    try:
        expected = _expected(manifest, wave, run_id)
        report["acquisition_id"] = manifest["acquisition_id"]
    except (TypeError, ValueError, KeyError) as exc:
        errors.append(f"frozen manifest invalid: {exc}")
        expected = {}

    if not isinstance(listing, dict) or not isinstance(listing.get("artifacts"), list):
        errors.append("GitHub artifact listing must contain an artifacts array")
        artifacts: list[Any] = []
    else:
        artifacts = listing["artifacts"]
        total = listing.get("total_count")
        if type(total) is not int or total != len(artifacts):
            errors.append(
                "artifact listing incomplete or total_count invalid "
                "(must fetch all pages)"
            )

    names: set[str] = set()
    ids: set[int] = set()
    seen: set[str] = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            errors.append(f"artifact[{index}] is not an object")
            continue
        name = artifact.get("name")
        if not isinstance(name, str) or not name:
            errors.append(f"artifact[{index}] has no valid name")
            continue
        if name in names:
            errors.append(f"duplicate artifact name: {name}")
        names.add(name)
        aid = artifact.get("id")
        if type(aid) is not int or aid <= 0:
            errors.append(f"invalid artifact id: {name}")
        elif aid in ids:
            errors.append(f"duplicate artifact id: {aid}")
        else:
            ids.add(aid)
        if not name.startswith(CASH_PREFIX):
            if name.startswith("okx-btc-"):
                report["unexpected_artifact_names"].append(name)
                errors.append(f"unexpected non-Cash preparation artifact: {name}")
            continue  # Control/summary artifacts are not Cash case evidence.
        if name not in expected:
            report["unexpected_artifact_names"].append(name)
            errors.append(f"unexpected Cash artifact: {name}")
            continue
        market_date, kind = expected[name]
        if name in seen:
            continue
        seen.add(name)
        report["verified_artifact_count_by_kind"][kind] += 1
        per_date = report["artifacts_by_market_date"].setdefault(market_date, {})
        per_date[kind] = {
            "name": name, "id": aid, "digest": artifact.get("digest"),
            "size_in_bytes": artifact.get("size_in_bytes"),
        }
        if artifact.get("expired") is not False:
            errors.append(f"expired or unknown expiry: {name}")
        size = artifact.get("size_in_bytes")
        if type(size) is not int or size <= 0:
            errors.append(f"missing/empty artifact size: {name}")
        digest = artifact.get("digest")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            errors.append(f"invalid Actions SHA-256 digest: {name}")
        workflow_run = artifact.get("workflow_run")
        if (
            not isinstance(workflow_run, dict)
            or str(workflow_run.get("id")) != run_id
        ):
            errors.append(f"artifact workflow_run does not match caller: {name}")

    missing = sorted(set(expected) - seen)
    report["missing_artifact_names"] = missing
    if missing:
        errors.append(f"missing {len(missing)} frozen Cash artifacts")
    if not errors:
        report["status"] = "verified_inventory_only"
    report["artifacts_by_market_date"] = dict(
        sorted(report["artifacts_by_market_date"].items())
    )
    report["unexpected_artifact_names"].sort()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--wave", choices=sorted(FROZEN_WAVES), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--acquisition-result", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        artifacts = json.loads(args.artifacts.read_text(encoding="utf-8"))
        report = verify_inventory(
            manifest, artifacts, wave=args.wave, run_id=args.run_id,
            acquisition_result=args.acquisition_result,
        )
    except (OSError, ValueError) as exc:
        report = {
            "schema_version": 1,
            "evidence_type": "cash_2025_quarter_preparation_boundary",
            "status": "failed",
            "errors": [f"inventory input error: {exc}"],
            "artifact_contents_verified": False,
            "corpus_mutation": False,
            "promotion_dispatched": False,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if report["status"] == "verified_inventory_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
