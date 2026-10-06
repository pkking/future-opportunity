from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from future_opportunity.backtest.acquisition import (
    acquisition_manifest_payload,
    load_historical_acquisition_manifest,
    workflow_cash_cases_json,
    workflow_funding_dates_json,
    workflow_funding_selection_provenance_json,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-funding-days", type=int, default=31)
    parser.add_argument("--max-cash-cases", type=int, default=31)
    parser.add_argument("--max-total-items", type=int, default=31)
    args = parser.parse_args()

    manifest = load_historical_acquisition_manifest(
        args.manifest,
        max_funding_days=args.max_funding_days,
        max_cash_cases=args.max_cash_cases,
        max_total_items=args.max_total_items,
    )
    payload = acquisition_manifest_payload(manifest)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")

    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a") as output:
            output.write(f"acquisition_id={manifest.acquisition_id}\n")
            output.write(
                f"planner_campaign_prefix={manifest.planner_campaign_prefix}\n"
            )
            output.write(
                f"funding_dates={workflow_funding_dates_json(manifest)}\n"
            )
            output.write(
                "funding_selection_provenance="
                + workflow_funding_selection_provenance_json(manifest)
                + "\n"
            )
            output.write(
                f"cash_cases={workflow_cash_cases_json(manifest)}\n"
            )
            output.write(
                f"funding_count={len(manifest.funding.market_dates) if manifest.funding else 0}\n"
            )
            output.write(f"cash_count={len(manifest.cash_cases)}\n")
            output.write(f"total_items={manifest.total_items}\n")


if __name__ == "__main__":
    main()
