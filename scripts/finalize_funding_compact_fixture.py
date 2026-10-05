from __future__ import annotations

import argparse
from pathlib import Path

from future_opportunity.backtest.funding_compact import (
    finalize_funding_compact_fixture,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--workflow-run", required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--artifact-digest", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    finalize_funding_compact_fixture(
        args.root,
        workflow_run=args.workflow_run,
        artifact_id=args.artifact_id,
        artifact_digest=args.artifact_digest,
    )


if __name__ == "__main__":
    main()
