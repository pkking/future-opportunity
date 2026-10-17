"""Produce a one-case research-only rescue manifest from the *approved* Cash Q2 cohort.

The selected 12-day population is immutable. This CLI only extracts the one
known source-capacity failure (2025-04-09) for separate operator approval; no
prices, outcomes, backups, exchange requests, or GitHub workflow dispatches.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from future_opportunity.backtest.acquisition import (
    acquisition_dispatch_payload,
    parse_historical_acquisition_manifest,
)
from validate_cash_2025q2_preparation_handoff import (
    AUDIT,
    CORPUS,
    MANIFEST,
    REGISTRY,
    WAVE,
    validate_handoff,
)

FAILED_DATE = "2025-04-09"
ENTRY_AT = "2025-04-09T00:15:00+00:00"
REPAIR_ACQUISITION_ID = "cash-2025q2-2025-04-09-source-repair-001"
REPAIR_PLANNER_PREFIX = "cash-2025q2-repair-001"


def resolve_source_cap_repair(
    frozen_wave: dict[str, Any],
    registration: dict[str, Any],
    member_audit: dict[str, Any],
    source_manifest: dict[str, Any],
    *,
    pinned_dates: list[str],
) -> dict[str, Any]:
    approved = validate_handoff(
        frozen_wave,
        registration,
        member_audit,
        source_manifest,
        pinned_dates=pinned_dates,
    )
    if approved["expected_cash_preparations"] != 12:
        raise ValueError("cannot repair without original approved 12-case source")
    candidates = [
        case for case in frozen_wave["cash_cases"]
        if case["entry_at"] == ENTRY_AT
    ]
    if len(candidates) != 1:
        raise ValueError("expected exactly one frozen 2025-04-09 failed source case")

    candidate = deepcopy(frozen_wave)
    candidate["acquisition_id"] = REPAIR_ACQUISITION_ID
    candidate["planner_campaign_prefix"] = REPAIR_PLANNER_PREFIX
    candidate["cash_cases"] = deepcopy(candidates)
    if (
        candidate["funding"] is not None
        or candidate["cash_cases"][0]["future_id"] != "BTC-USDT-250627"
        or candidate["cash_cases"][0]["exit_at"] != "2025-06-26T00:15:00+00:00"
        or candidate["cash_cases"][0]["expiry_at"] != "2025-06-27T08:00:00+00:00"
    ):
        raise ValueError("recovery must use the already frozen contract and exit")
    # Preserve *all twelve* original selection dates in provenance; do not
    # redefine the sampling population merely because only one date retries.
    if (
        candidate["selection_provenance"]
        != frozen_wave["selection_provenance"]
    ):
        raise ValueError("recovery cannot rewrite selection provenance")
    parsed = parse_historical_acquisition_manifest(
        candidate, max_funding_days=1, max_cash_cases=1, max_total_items=1
    )
    if parsed.total_items != 1 or parsed.funding is not None:
        raise ValueError("operator recovery must contain exactly one Cash case")
    payload = acquisition_dispatch_payload(parsed)
    if payload != candidate:
        raise ValueError("source recovery manifest differs from dispatch serializer")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--control-output", type=Path)
    args = parser.parse_args()

    corpus = json.loads(CORPUS.read_text())
    pinned = [
        item["entry_market_date"] for item in corpus["entries"]
        if item["strategy"] == "cash-and-carry"
    ]
    wave = resolve_source_cap_repair(
        json.loads(WAVE.read_text()),
        json.loads(REGISTRY.read_text()),
        json.loads(AUDIT.read_text()),
        json.loads(MANIFEST.read_text()),
        pinned_dates=pinned,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(wave, indent=2, sort_keys=True) + "\n")
    if args.control_output is not None:
        control = {
            "schema_version": 1,
            "evidence_type": "cash_2025q2_single_missing_source_repair_control",
            "source_research_run": "39079100154",
            "source_cap_failure_job_id": "117532314621",
            "failed_market_date": FAILED_DATE,
            "repair_acquisition_id": REPAIR_ACQUISITION_ID,
            "approved_selection_date_count": 12,
            "repair_case_count": 1,
            "selection_evidence_sha256":
                wave["selection_provenance"]["cash"]["sampling"]["evidence_sha256"],
            "human_repair_dispatch_approved": False,
            "repair_dispatched": False,
            "other_eleven_dates_untouched": True,
            "replace_failed_date_with_alternative": False,
            "promotion_approved": False,
            "live_trading_enabled": False,
        }
        args.control_output.parent.mkdir(parents=True, exist_ok=True)
        args.control_output.write_text(
            json.dumps(control, indent=2, sort_keys=True) + "\n"
        )
    print(json.dumps({
        "repair_date": FAILED_DATE,
        "number_of_cases": 1,
        "separate_operator_authorization_required": True,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
