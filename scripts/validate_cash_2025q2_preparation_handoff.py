"""Offline fail-closed control for the authorized-but-not-dispatched Cash 2025Q2 wave.

This utility never calls an exchange or starts any GitHub workflow. Human
approval of the date freeze does not authorize the separate L2 acquisition.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from future_opportunity.backtest.acquisition import (
    acquisition_dispatch_payload,
    parse_historical_acquisition_manifest,
)
from validate_cash_2025q2_preregistration import (
    AUDIT, CORPUS, MANIFEST, REGISTRY, validate_selection,
)

ROOT = Path(__file__).parents[1]
WAVE = ROOT / "docs/historical-acquisition-plans/cash-2025q2-12day-wave-001.json"
SELECTION_SOURCE = {
    "workflow_run": "39050630845",
    "artifact_name": "cash-2025q2-approved-selection-control",
    "artifact_id": "12106828444",
    "artifact_digest": "sha256:8f29acfacaa71d1e5a59c0a0b28e28eef43257e6613c5cfa4806fea4740c9e36",
}
SELECTION_DIGEST = "9bd08184a3a0c2487ba57087effdf0e8231db45fb4bf10226290627ed2990b37"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def validate_handoff(
    raw: dict[str, Any],
    registration: dict[str, Any],
    audit: dict[str, Any],
    source_manifest: dict[str, Any],
    *,
    pinned_dates: list[str],
) -> dict[str, Any]:
    accepted = validate_selection(
        registration, audit, source_manifest, pinned_dates=pinned_dates
    )
    require(
        raw.get("acquisition_id") == "cash-2025q2-12day-wave-001"
        and raw.get("planner_campaign_prefix") == "cash-2025q2-review-001"
        and raw.get("funding") is None,
        "Cash Q2 handoff must be the exact frozen cash-only wave",
    )
    source = raw.get("selection_provenance")
    require(isinstance(source, dict) and set(source) == {"funding", "cash"}
            and source["funding"] is None
            and isinstance(source["cash"], dict),
            "Cash Q2 handoff requires only registered Cash provenance")
    cash = source["cash"]
    require(
        cash.get("schema_version") == 1
        and cash.get("selection_kind") == "pre_registered_availability_sample"
        and cash.get("strategy") == "cash-and-carry"
        and cash.get("source") == SELECTION_SOURCE,
        "Cash Q2 provenance must reference exact audited approval artifact",
    )
    require(cash.get("sampling") == {
        "policy_version": "availability-even-rank-v1",
        "start_date": "2025-03-29",
        "end_date": "2025-06-26",
        "requested_sample_size": 12,
        "population_size": 89,
        "excluded_market_dates": ["2025-06-26"],
        "selected_market_dates": accepted["selected_market_dates"],
        "evidence_sha256": SELECTION_DIGEST,
    }, "Cash Q2 source-bound sampling evidence differs from approved selection")
    cases = raw.get("cash_cases")
    require(isinstance(cases, list) and len(cases) == 12,
            "Cash Q2 must prepare exactly 12 frozen cases")
    expected = [
        {
            "entry_at": day + "T00:15:00+00:00",
            "exit_at": "2025-06-26T00:15:00+00:00",
            "future_id": "BTC-USDT-250627",
            "expiry_at": "2025-06-27T08:00:00+00:00",
        }
        for day in accepted["selected_market_dates"]
    ]
    require(cases == expected, "Cash Q2 case set, dates or entry/exit timestamps drifted")
    parsed = parse_historical_acquisition_manifest(
        raw, max_funding_days=1, max_cash_cases=12, max_total_items=12
    )
    require(parsed.funding is None and parsed.total_items == 12
            and parsed.cash_selection_provenance is not None
            and parsed.cash_selection_provenance.sampling_evidence_sha256 == SELECTION_DIGEST,
            "existing acquisition/selection parser rejected frozen plan")
    payload = acquisition_dispatch_payload(parsed)
    require(payload == raw, "acquisition dispatch serializer changed frozen plan")
    return {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_operator_preparation_handoff",
        "acquisition_id": parsed.acquisition_id,
        "approved_selection_source": SELECTION_SOURCE,
        "selected_market_dates": accepted["selected_market_dates"],
        "expected_cash_preparations": 12,
        "ready_for_human_authorization": True,
        "historical_acquisition_dispatched": False,
        "l2_sampled_for_selected_cases": False,
        "promotion_approved": False,
        "live_trading_enabled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads(CORPUS.read_text())
    pinned = [x["entry_market_date"] for x in corpus["entries"]
              if x["strategy"] == "cash-and-carry"]
    result = validate_handoff(
        json.loads(WAVE.read_text()), json.loads(REGISTRY.read_text()),
        json.loads(AUDIT.read_text()), json.loads(MANIFEST.read_text()),
        pinned_dates=pinned,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"date_count": result["expected_cash_preparations"],
                      "dispatched": False, "human_authorization_required": True}))


if __name__ == "__main__":
    main()
