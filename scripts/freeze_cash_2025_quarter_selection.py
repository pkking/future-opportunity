from __future__ import annotations

import argparse
import json
from pathlib import Path

from future_opportunity.backtest.cash_prior_quarter_selection import (
    validate_cash_prior_quarter_preregistration,
)


ROOT = Path(__file__).parents[1]
SELECTION = ROOT / "docs/historical-acquisition-plans/cash-2025-q3q4-24day-preregistration-v1.json"
INDEX = ROOT / "tests/fixtures/historical/corpus-index.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(SELECTION.read_text())
    index = json.loads(INDEX.read_text())
    dates = [
        entry["entry_market_date"]
        for entry in index["entries"]
        if entry["strategy"] == "cash-and-carry"
    ]
    evidence = validate_cash_prior_quarter_preregistration(
        raw, pinned_cash_market_dates=dates,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "selected_count": evidence["selected_market_date_count"],
        "quarter_evidence": [
            {
                "quarter": item["quarter"],
                "population_size": item["population_size"],
                "evidence_sha256": item["selection_evidence_sha256"],
            }
            for item in evidence["quarters"]
        ],
        "acquisition_approved": False,
        "promotion_approved": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
