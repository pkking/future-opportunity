from __future__ import annotations

import argparse
import json
import os
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

from future_opportunity.backtest.campaign import (
    ResolvedHistoricalCampaignItem,
    load_historical_campaign_manifest,
    promote_historical_campaign,
)
from future_opportunity.backtest.evidence import write_backtest_evidence
from future_opportunity.backtest.historical_policy import (
    distribution_transition_readiness,
    load_historical_acceptance_policy,
)


def _load_resolved(
    path: Path,
    *,
    expected_items,
) -> tuple[ResolvedHistoricalCampaignItem, ...]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("unsupported resolved historical campaign schema")
    raw_items = raw.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("resolved historical campaign requires items")
    if len(raw_items) != len(expected_items):
        raise ValueError(
            "resolved campaign item count differs from operator manifest"
        )

    resolved: list[ResolvedHistoricalCampaignItem] = []
    for position, (raw_item, expected) in enumerate(
        zip(raw_items, expected_items, strict=True)
    ):
        if not isinstance(raw_item, dict):
            raise TypeError(
                f"resolved campaign item {position} must be an object"
            )
        expected_keys = {
            "source_root",
            "source_workflow_run",
            "compact_artifact_name",
            "parent_artifact_id",
            "parent_artifact_sha256",
        }
        if set(raw_item) != expected_keys:
            raise ValueError(
                f"resolved campaign item {position} fields differ from schema"
            )
        run = raw_item.get("source_workflow_run")
        name = raw_item.get("compact_artifact_name")
        if run != expected.source_workflow_run:
            raise ValueError(
                f"resolved campaign item {position} source run drifted"
            )
        if name != expected.compact_artifact_name:
            raise ValueError(
                f"resolved campaign item {position} artifact name drifted"
            )

        values: dict[str, str] = {}
        for key in expected_keys:
            value = raw_item.get(key)
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"resolved campaign item {position} requires {key}"
                )
            values[key] = value
        resolved.append(
            ResolvedHistoricalCampaignItem(
                source_root=Path(values["source_root"]),
                source_workflow_run=values["source_workflow_run"],
                compact_artifact_name=values["compact_artifact_name"],
                parent_artifact_id=values["parent_artifact_id"],
                parent_artifact_sha256=values["parent_artifact_sha256"],
            )
        )
    return tuple(resolved)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    parser.add_argument("resolved", type=Path)
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=Path("tests/fixtures/historical"),
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("tests/fixtures/historical/corpus-index.json"),
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("tests/e2e/historical-target-policy.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/historical-campaign/promotion.json"),
    )
    parser.add_argument("--max-items", type=int, default=31)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    try:
        campaign = load_historical_campaign_manifest(
            args.campaign,
            max_items=args.max_items,
        )
        resolved = _load_resolved(
            args.resolved,
            expected_items=campaign.items,
        )
        policy, _ = load_historical_acceptance_policy(args.policy)
        result = promote_historical_campaign(
            resolved,
            fixture_root=args.fixture_root,
            index_path=args.index,
            required_strategies=policy.required_strategies,
        )
        readiness = distribution_transition_readiness(
            policy,
            dict(result.entry_days_by_strategy),
        )

        evidence: dict[str, Any] = {
            "schema_version": 1,
            "evidence_type": "historical_corpus_campaign_promotion",
            "campaign_id": campaign.campaign_id,
            "status": result.status,
            "items": [
                {
                    "source_workflow_run": source.source_workflow_run,
                    "compact_artifact_name": source.compact_artifact_name,
                    "promotion": asdict(item_result),
                }
                for source, item_result in zip(
                    resolved,
                    result.items,
                    strict=True,
                )
            ],
            "readiness": asdict(readiness),
        }
        write_backtest_evidence(evidence, args.output)

        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with Path(github_output).open("a") as output:
                output.write(f"campaign_id={campaign.campaign_id}\n")
                output.write(
                    f"changed={'true' if result.status == 'staged' else 'false'}\n"
                )
                output.write(
                    f"funding_days={readiness.counts().get('funding-carry', 0)}\n"
                )
                output.write(
                    f"cash_days={readiness.counts().get('cash-and-carry', 0)}\n"
                )
                output.write(
                    f"minimum_ready={'true' if readiness.minimum_ready else 'false'}\n"
                )
                output.write(
                    f"preferred_ready={'true' if readiness.preferred_ready else 'false'}\n"
                )
    except Exception as error:
        write_backtest_evidence(
            {
                "schema_version": 1,
                "evidence_type": "historical_corpus_campaign_promotion",
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
            },
            args.output,
        )
        raise


if __name__ == "__main__":
    main()
