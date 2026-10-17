"""Emit the source-only official control for the approved Cash 2025Q2 date sample.

The full catalog/member population, fixed 12 dates and human approval have
already been frozen and reviewed in PR #101. This does not acquire books,
evaluate trading economics or authorize corpus promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from validate_cash_2025q2_preregistration import (
    AUDIT, CORPUS, MANIFEST, REGISTRY, validate_selection,
)

APPROVED_PR = "https://github.com/pkking/future-opportunity/pull/101"
APPROVED_MERGE_COMMIT = "4acf3e945769d49dd001b686ad1cd114f5bb32f8"
APPROVED_MAIN_CI_RUN = "39050288482"
EXPECTED_SELECTED = (
    "2025-04-01", "2025-04-09", "2025-04-16", "2025-04-23",
    "2025-05-01", "2025-05-08", "2025-05-16", "2025-05-23",
    "2025-05-31", "2025-06-07", "2025-06-14", "2025-06-22",
)
EXPECTED_SELECTION_SHA = "9bd08184a3a0c2487ba57087effdf0e8231db45fb4bf10226290627ed2990b37"


def build_control(
    registry: dict[str, Any], member_audit: dict[str, Any],
    manifest: dict[str, Any], *, pinned_dates: list[str],
    registration_sha256: str,
) -> dict[str, Any]:
    verified = validate_selection(registry, member_audit, manifest, pinned_dates=pinned_dates)
    if (
        tuple(verified["selected_market_dates"]) != EXPECTED_SELECTED
        or verified["selection_evidence_sha256"] != EXPECTED_SELECTION_SHA
        or not isinstance(registration_sha256, str)
        or len(registration_sha256) != 64
        or any(c not in "0123456789abcdef" for c in registration_sha256)
    ):
        raise ValueError("approved source-bound registration or SHA mismatch")
    return {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_frozen_source_bound_selection_control",
        "strategy": "cash-and-carry",
        "future_id": "BTC-USDT-250627",
        "registration_path": "docs/historical-acquisition-plans/cash-2025q2-12day-preregistration-v1.json",
        "registration_sha256": registration_sha256,
        "approval_pr": APPROVED_PR,
        "approval_merge_commit": APPROVED_MERGE_COMMIT,
        "approval_main_ci_run": APPROVED_MAIN_CI_RUN,
        "selection_kind": "pre_registered_availability_sample",
        "selection_policy_version": "availability-even-rank-v1",
        "selection_evidence_sha256": EXPECTED_SELECTION_SHA,
        "source_member_run": "39045070860",
        "source_member_artifact_manifest_sha256": registry["source_evidence"]["member_artifact_manifest_sha256"],
        "start_date": registry["start_date"],
        "end_date": registry["end_date"],
        "excluded_market_dates": ["2025-06-26"],
        "population_size": 89,
        "requested_sample_size": 12,
        "selected_market_dates": list(EXPECTED_SELECTED),
        "entry_time_utc": "00:15:00",
        "exit_at": registry["exit_at"],
        "expiry_at": registry["expiry_at"],
        "historical_selection_frozen": True,
        "member_source_verified_for_calendar": True,
        "sampled_l2_verified": False,
        "economic_outcomes_inspected": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "live_trading_enabled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    registry_bytes = REGISTRY.read_bytes()
    corpus = json.loads(CORPUS.read_text())
    pinned = [item["entry_market_date"] for item in corpus["entries"]
              if item["strategy"] == "cash-and-carry"]
    report = build_control(
        json.loads(registry_bytes),
        json.loads(AUDIT.read_text()),
        json.loads(MANIFEST.read_text()),
        pinned_dates=pinned,
        registration_sha256=hashlib.sha256(registry_bytes).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "registration_sha256": report["registration_sha256"],
        "selected_count": len(report["selected_market_dates"]),
        "selection_frozen": True,
        "acquisition_approved": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
