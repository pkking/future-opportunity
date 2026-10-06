from __future__ import annotations

import argparse
import asyncio
import json
import traceback
from pathlib import Path

from future_opportunity.backtest.distribution_report import (
    build_historical_corpus_distribution,
)
from future_opportunity.backtest.evidence import write_backtest_evidence


ROOT = Path(__file__).parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produce reporting-only distributions over all pinned history"
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=ROOT / "tests/fixtures/historical",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=ROOT / "tests/fixtures/historical/corpus-index.json",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=ROOT / "tests/e2e/historical-target-policy.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/historical-smoke/corpus-distribution.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    try:
        report = asyncio.run(
            build_historical_corpus_distribution(
                fixture_root=args.fixture_root,
                index_path=args.index,
                policy_path=args.policy,
            )
        )
        write_backtest_evidence(report, args.output)
        print(
            json.dumps(
                {
                    "evidence_type": report["evidence_type"],
                    "economics_gate": report["economics_gate"],
                    "pinned_case_counts": {
                        strategy: summary["evaluated_case_count"]
                        for strategy, summary in report["strategies"].items()
                    },
                    "output": str(args.output),
                },
                sort_keys=True,
            )
        )
    except Exception as error:
        write_backtest_evidence(
            {
                "schema_version": 1,
                "evidence_type": "historical_corpus_distribution_actuals",
                "economics_gate": "reporting_only",
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
