from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from future_opportunity.backtest.campaign_inventory import (
    selection_provenance_sha256,
    verified_candidates_from_inventory,
)
from future_opportunity.backtest.campaign_planning import (
    plan_historical_campaigns,
)
from future_opportunity.backtest.corpus import load_historical_corpus
from future_opportunity.backtest.historical_policy import (
    load_historical_acceptance_policy,
)
def _excluded_pinned_evidence(
    candidate,
    *,
    corpus,
    fixture_root: Path,
    inventory_evidence: list[dict[str, str]],
) -> dict[str, str]:
    pinned = next(
        entry
        for entry in corpus.entries
        if entry.strategy == candidate.entry.strategy
        and entry.entry_market_date == candidate.entry.entry_market_date
    )
    candidate_record = next(
        item
        for item in inventory_evidence
        if item["dataset_id"] == candidate.entry.dataset_id
    )
    candidate_sha = candidate_record["selection_provenance_sha256"]
    pinned_sha = selection_provenance_sha256(
        fixture_root / pinned.fixture_path / "manifest.json"
    )

    if candidate_sha == "absent":
        status = "candidate_missing"
    elif pinned_sha == "absent":
        status = "pinned_missing"
    elif candidate_sha == pinned_sha:
        status = "match"
    else:
        status = "different"

    return {
        "dataset_id": candidate.entry.dataset_id,
        "strategy": candidate.entry.strategy,
        "entry_market_date": candidate.entry.entry_market_date,
        "reason": "pinned_by_identity",
        "candidate_selection_provenance_sha256": candidate_sha,
        "pinned_selection_provenance_sha256": pinned_sha,
        "selection_provenance_status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--campaign-prefix", required=True)
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=Path("tests/fixtures/historical"),
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("tests/e2e/historical-target-policy.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/historical-campaign-planner"),
    )
    parser.add_argument("--wave-size", type=int, default=31)
    args = parser.parse_args()

    policy, _ = load_historical_acceptance_policy(args.policy)
    corpus = load_historical_corpus(
        index_path=args.fixture_root / "corpus-index.json",
        fixture_root=args.fixture_root,
        required_strategies=policy.required_strategies,
    )
    candidates, evidence = verified_candidates_from_inventory(args.inventory)
    planned = plan_historical_campaigns(
        candidates,
        corpus=corpus,
        policy=policy,
        campaign_prefix=args.campaign_prefix,
        max_items_per_wave=args.wave_size,
    )

    wave_dir = args.output_dir / "waves"
    wave_dir.mkdir(parents=True, exist_ok=True)
    for wave in planned.waves:
        (wave_dir / f"{wave.campaign_id}.json").write_text(
            json.dumps(asdict(wave), indent=2) + "\n"
        )

    report = {
        "schema_version": 1,
        "evidence_type": "read_only_historical_campaign_planner",
        "status": "planned",
        "does_not_promote": True,
        "campaign_prefix": args.campaign_prefix,
        "pinned_counts": dict(planned.pinned_counts),
        "projected_counts_if_all_waves_merged": dict(planned.projected_counts),
        "minimum_ready_now": planned.minimum_ready_now,
        "minimum_ready_if_merged": planned.minimum_ready_if_merged,
        "preferred_ready_now": planned.preferred_ready_now,
        "preferred_ready_if_merged": planned.preferred_ready_if_merged,
        "wave_count": len(planned.waves),
        "selected_count": len(planned.selected),
        "excluded_pinned_count": len(planned.excluded_pinned),
        "selected": [
            {
                "source_workflow_run": candidate.source_workflow_run,
                "compact_artifact_name": candidate.compact_artifact_name,
                "dataset_id": candidate.entry.dataset_id,
                "strategy": candidate.entry.strategy,
                "entry_market_date": candidate.entry.entry_market_date,
            }
            for candidate in planned.selected
        ],
        "excluded_pinned": [
            _excluded_pinned_evidence(
                candidate,
                corpus=corpus,
                fixture_root=args.fixture_root,
                inventory_evidence=evidence,
            )
            for candidate in planned.excluded_pinned
        ],
        "verified_source_evidence": evidence,
        "wave_files": [
            f"waves/{wave.campaign_id}.json"
            for wave in planned.waves
        ],
        "note": (
            "Forecast is not current pinned readiness; open PRs do not count. "
            "Every wave still requires explicit promotion, PR checks, and human merge."
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "pinned_counts": report["pinned_counts"],
        "projected_counts_if_all_waves_merged": report[
            "projected_counts_if_all_waves_merged"
        ],
        "selected_count": report["selected_count"],
        "excluded_pinned_count": report["excluded_pinned_count"],
        "wave_files": report["wave_files"],
    }, indent=2))

    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a") as output:
            output.write(f"wave_count={len(planned.waves)}\n")
            output.write(f"selected_count={len(planned.selected)}\n")


if __name__ == "__main__":
    main()
