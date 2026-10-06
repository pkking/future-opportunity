from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from future_opportunity.backtest.promotion import (
    promote_historical_compact_fixture,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
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
    parser.add_argument("--source-workflow-run")
    parser.add_argument("--parent-artifact-id")
    parser.add_argument("--parent-artifact-sha256")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = promote_historical_compact_fixture(
        args.source,
        fixture_root=args.fixture_root,
        index_path=args.index,
        source_workflow_run=args.source_workflow_run,
        expected_parent_artifact_id=args.parent_artifact_id,
        expected_parent_artifact_sha256=args.parent_artifact_sha256,
    )
    payload = asdict(result)
    print(json.dumps(payload, indent=2, sort_keys=True))

    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a") as output:
            output.write(f"status={result.status}\n")
            output.write(f"dataset_id={result.entry.dataset_id}\n")
            output.write(f"strategy={result.entry.strategy}\n")
            output.write(
                f"entry_market_date={result.entry.entry_market_date}\n"
            )
            output.write(f"fixture_path={result.entry.fixture_path}\n")
            output.write(
                f"changed={'true' if result.status == 'staged' else 'false'}\n"
            )


if __name__ == "__main__":
    main()
