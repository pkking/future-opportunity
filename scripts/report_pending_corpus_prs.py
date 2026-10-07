"""Create read-only evidence about overlapping open corpus PR proposals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from future_opportunity.backtest.historical_policy import (
    load_historical_acceptance_policy,
)
from future_opportunity.backtest.pending_review import (
    PendingCorpusProposal,
    analyze_pending_corpus_prs,
    parse_corpus_index_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-index",
        type=Path,
        default=REPO_ROOT / "tests/fixtures/historical/corpus-index.json",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=REPO_ROOT / "tests/e2e/historical-target-policy.json",
    )
    parser.add_argument("--proposals-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    policy, _ = load_historical_acceptance_policy(args.policy)

    baseline = parse_corpus_index_snapshot(
        json.loads(args.base_index.read_text()),
        required_strategies=policy.required_strategies,
    )
    if not args.proposals_dir.is_dir():
        raise ValueError("proposals directory must exist")

    proposals: list[PendingCorpusProposal] = []
    for path in sorted(args.proposals_dir.glob("*.json")):
        value: Any = json.loads(path.read_text())
        if not isinstance(value, dict) or set(value) != {
            "pr_number",
            "head_sha",
            "index",
        }:
            raise ValueError(
                f"invalid pending PR evidence envelope: {path.name}"
            )
        number, sha = value["pr_number"], value["head_sha"]
        if type(number) is not int or not isinstance(sha, str):
            raise TypeError(f"invalid PR identity: {path.name}")
        proposals.append(
            PendingCorpusProposal(
                pr_number=number,
                head_sha=sha,
                index=parse_corpus_index_snapshot(
                    value["index"],
                    required_strategies=policy.required_strategies,
                ),
            )
        )

    report = analyze_pending_corpus_prs(
        baseline,
        tuple(proposals),
        policy=policy,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "pinned_counts": dict(report.pinned_counts),
                "pending_pr_count": len(report.proposals),
                "projected_union_counts_if_all_approved": dict(
                    report.projected_union_counts_if_all_approved
                ),
                "overlap_count": len(report.overlaps),
                "conflicting_pending_facts": report.conflicting_pending_facts,
                "shared_index_reconciliation_required": (
                    report.shared_index_reconciliation_required
                ),
                "output": str(args.output),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
