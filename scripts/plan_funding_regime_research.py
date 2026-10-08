from __future__ import annotations

import argparse
import json
from pathlib import Path

from future_opportunity.backtest.funding_regime_research import (
    plan_funding_regime_research,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research-only pre-entry Funding regime sampling"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("input and output paths must differ")

    raw = json.loads(args.input.read_text())
    result = plan_funding_regime_research(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "research_only": True,
                "quota_fully_met": result["quota_fully_met"],
                "selected_count": len(result["selected_dates"]),
                "source_authentication_status": result["source_authentication_status"],
                "evidence_sha256": result["evidence_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
