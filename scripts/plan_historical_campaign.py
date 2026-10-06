from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from future_opportunity.backtest.campaign_planning import (
    VerifiedHistoricalCandidate,
    plan_historical_campaigns,
)
from future_opportunity.backtest.corpus import load_historical_corpus
from future_opportunity.backtest.historical_policy import (
    load_historical_acceptance_policy,
)
from future_opportunity.backtest.promotion import (
    inspect_historical_compact_fixture,
)


_SHA256 = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_KEYS = {
    "source_root",
    "source_workflow_run",
    "compact_artifact_name",
    "compact_artifact_id",
    "compact_artifact_digest",
    "parent_artifact_id",
    "parent_artifact_sha256",
}


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"planner inventory requires {key}")
    return value


def verified_candidates_from_inventory(
    path: Path,
) -> tuple[tuple[VerifiedHistoricalCandidate, ...], list[dict[str, str]]]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "items"}:
        raise ValueError("invalid planner inventory fields")
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        raise ValueError("unsupported planner inventory schema")
    raw_items = raw.get("items")
    if not isinstance(raw_items, list):
        raise TypeError("planner inventory items must be an array")
    if len(raw_items) > 620:
        raise ValueError("planner inventory exceeds 620 compact artifacts")

    candidates: list[VerifiedHistoricalCandidate] = []
    evidence: list[dict[str, str]] = []
    for idx, item in enumerate(raw_items):
        if not isinstance(item, dict) or set(item) != _KEYS:
            raise ValueError(f"planner inventory item {idx} fields differ from schema")
        fields = {key: _required_string(item, key) for key in _KEYS}
        for key in ("source_workflow_run", "compact_artifact_id", "parent_artifact_id"):
            if not fields[key].isdigit():
                raise ValueError(f"planner inventory item {idx} {key} must be numeric")
        for key in ("compact_artifact_digest", "parent_artifact_sha256"):
            if _SHA256.fullmatch(fields[key]) is None:
                raise ValueError(f"planner inventory item {idx} {key} invalid SHA-256")
        entry = inspect_historical_compact_fixture(
            Path(fields["source_root"]),
            source_workflow_run=fields["source_workflow_run"],
            expected_parent_artifact_id=fields["parent_artifact_id"],
            expected_parent_artifact_sha256=fields["parent_artifact_sha256"],
        )
        candidates.append(
            VerifiedHistoricalCandidate(
                source_workflow_run=fields["source_workflow_run"],
                compact_artifact_name=fields["compact_artifact_name"],
                entry=entry,
            )
        )
        evidence.append({
            "source_workflow_run": fields["source_workflow_run"],
            "compact_artifact_name": fields["compact_artifact_name"],
            "compact_artifact_id": fields["compact_artifact_id"],
            "compact_artifact_digest": fields["compact_artifact_digest"],
            "parent_artifact_id": fields["parent_artifact_id"],
            "parent_artifact_sha256": fields["parent_artifact_sha256"],
            "dataset_id": entry.dataset_id,
            "strategy": entry.strategy,
            "entry_market_date": entry.entry_market_date,
        })
    return tuple(candidates), evidence


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
            {
                "dataset_id": candidate.entry.dataset_id,
                "strategy": candidate.entry.strategy,
                "entry_market_date": candidate.entry.entry_market_date,
                "reason": "pinned_by_identity_content_not_compared",
            }
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
