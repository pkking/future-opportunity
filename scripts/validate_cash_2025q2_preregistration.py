"""Fail-closed, outcome-blind validator of proposed Cash 2025Q2 N=12 preregistration.

Never launches source acquisition, strategy replay, corpus promotion or trading.
A green validation is NOT independent approval of the review PR.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from future_opportunity.backtest.availability_selection import (
    POLICY_VERSION,
    AvailabilitySelectionRequest,
    replay_availability_selection,
)

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "docs/historical-acquisition-plans/cash-2025q2-12day-preregistration-v1.json"
MANIFEST = ROOT / "docs/research/cash-2025q2-member-artifacts-manifest-v1.json"
AUDIT = ROOT / "docs/research/cash-2025q2-member-population-audit-v1.json"
CORPUS = ROOT / "tests/fixtures/historical/corpus-index.json"
MANIFEST_SHA = "88669cef7860f616b0483723c07edea82040bd86033a61bcc55a51bf4eb41b72"
AUDIT_SHA = "6030971d2060c603d6ce78222d68e0ea1f7a040f0c099b108fbf88247a298c6c"
CATALOG_SHA = "1b9a4adcb7035ca4abb70e5a9f1823dc3a71f5e9849070ce59c493df205b57ae"


def demand(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def validate_selection(
    raw: dict[str, Any], audit: dict[str, Any],
    manifest: dict[str, Any], *, pinned_dates: Sequence[str],
) -> dict[str, Any]:
    demand(isinstance(raw, dict) and set(raw) == {
        "schema_version", "evidence_type", "study_id", "strategy", "future_id",
        "start_date", "end_date", "entry_time_utc", "exit_at", "expiry_at",
        "source_evidence", "selection_policy_version", "source_unavailable_market_dates",
        "excluded_market_dates", "excluded_market_date_reasons",
        "eligible_population_size", "requested_sample_size",
        "selected_market_dates", "selection_evidence_sha256", "invariants",
    }, "Cash source-bound preregistration fields mismatch")
    demand(
        raw["schema_version"] == 1
        and raw["evidence_type"] == "cash_2025q2_pre_registered_availability_selection"
        and raw["study_id"] == "cash-2025-q2-250627-source-availability-v1"
        and raw["strategy"] == "cash-and-carry"
        and raw["future_id"] == "BTC-USDT-250627"
        and raw["start_date"] == "2025-03-29"
        and raw["end_date"] == "2025-06-26"
        and raw["entry_time_utc"] == "00:15:00"
        and raw["exit_at"] == "2025-06-26T00:15:00+00:00"
        and raw["expiry_at"] == "2025-06-27T08:00:00+00:00"
        and raw["selection_policy_version"] == POLICY_VERSION
        and type(raw["requested_sample_size"]) is int
        and raw["requested_sample_size"] == 12,
        "frozen study, contract, policy or time boundaries mismatch",
    )
    demand(raw["source_evidence"] == {
        "catalog_run": "39038071038",
        "catalog_artifact_id": "12103210971",
        "catalog_zip_sha256": CATALOG_SHA,
        "member_run": "39045070860",
        "member_head_sha": "b5980b907d8e698906ef4fe49de18fba6b451cf6",
        "member_artifact_manifest_path":
            "docs/research/cash-2025q2-member-artifacts-manifest-v1.json",
        "member_artifact_manifest_sha256": MANIFEST_SHA,
        "member_population_audit_path":
            "docs/research/cash-2025q2-member-population-audit-v1.json",
        "member_population_audit_sha256": AUDIT_SHA,
    }, "unrecognized official source run, artifact or immutable SHA")
    demand(raw["invariants"] == {
        "outcomes_not_inspected_for_selection": True,
        "independent_human_preregistration_review_required": True,
        "no_outcome_based_replacement": True,
        "selected_l2_not_yet_verified": True,
        "automatic_acquisition": False,
        "automatic_promotion": False,
        "stage2_economics_gate_enabled": False,
        "live_trading_enabled": False,
    }, "proposed sampling safety constraints have changed")
    demand(
        manifest["member_source_run"] == "39045070860"
        and manifest["source_catalog_sha256"] == CATALOG_SHA
        and len(manifest["batches"]) == 9
        and audit["member_source_run"] == manifest["member_source_run"]
        and audit["member_source_head_sha"] == manifest["member_source_head_sha"]
        and audit["source_catalog_sha256"] == CATALOG_SHA
        and audit["complete_member_population_verified"] is True
        and audit["counts"] == {
            "identity_verified": 90, "unavailable": 0, "ambiguous": 0, "error": 0
        }
        and audit["source_unavailable_dates"] == []
        and audit["verified_member_available_dates"] == audit["frozen_calendar_dates"]
        and len(audit["frozen_calendar_dates"]) == 90
        and audit["sample_selection_frozen"] is False
        and audit["l2_orderbook_verified"] is False
        and audit["economics_evaluated"] is False
        and audit["acquisition_approved"] is False
        and audit["promotion_approved"] is False,
        "exact future-member population is not fully verified, or is promoted",
    )
    demand(raw["source_unavailable_market_dates"] == []
           and raw["excluded_market_dates"] == ["2025-06-26"]
           and raw["excluded_market_date_reasons"] == {
               "2025-06-26": "entry_0015_equals_fixed_exit_0015",
           }, "an exit date or missing source date was silently misclassified")
    exit_at = datetime.fromisoformat(raw["exit_at"]).astimezone(UTC)
    expiry_at = datetime.fromisoformat(raw["expiry_at"]).astimezone(UTC)
    demand(exit_at < expiry_at, "expiry must follow fixed exit")
    replay = replay_availability_selection(AvailabilitySelectionRequest(
        strategy="cash-and-carry",
        start_date=raw["start_date"],
        end_date=raw["end_date"],
        excluded_market_dates=tuple(raw["excluded_market_dates"]),
        sample_size=raw["requested_sample_size"],
    ))
    demand(len(replay.eligible_market_dates) == 89
           and raw["eligible_population_size"] == replay.population_size
           and list(replay.eligible_market_dates) == audit["frozen_calendar_dates"][:-1]
           and list(replay.selected_market_dates) == raw["selected_market_dates"]
           and replay.evidence_sha256 == raw["selection_evidence_sha256"],
           "source-bound eligible population, deterministic sample or SHA disagree")
    pinned = set(pinned_dates)
    demand(len(pinned) == len(pinned_dates), "pinned Cash dates contain duplicates")
    for market_date in replay.selected_market_dates:
        entry_at = datetime.fromisoformat(market_date + "T00:15:00+00:00")
        demand(entry_at < exit_at and market_date not in pinned,
               "sampled entry collides with fixed exit or pinned corpus")
    return {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_source_bound_preregistration_validation",
        "selected_market_dates": list(replay.selected_market_dates),
        "eligible_population_size": replay.population_size,
        "selection_evidence_sha256": replay.evidence_sha256,
        "independent_human_review_required": True,
        "historical_selection_approved": False,
        "complete_selected_l2_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    demand(hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == MANIFEST_SHA,
           "immutable nine-source artifact manifest SHA differs")
    demand(hashlib.sha256(AUDIT.read_bytes()).hexdigest() == AUDIT_SHA,
           "immutable source-member population SHA differs")
    pinned = [
        item["entry_market_date"]
        for item in json.loads(CORPUS.read_text())["entries"]
        if item["strategy"] == "cash-and-carry"
    ]
    result = validate_selection(
        json.loads(REGISTRY.read_text()),
        json.loads(AUDIT.read_text()),
        json.loads(MANIFEST.read_text()),
        pinned_dates=pinned,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"candidate_days": result["eligible_population_size"],
                      "proposed_selected_days": len(result["selected_market_dates"]),
                      "independent_review_required": True}, sort_keys=True))


if __name__ == "__main__":
    main()
