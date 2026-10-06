from __future__ import annotations

import argparse
import json
from pathlib import Path

from future_opportunity.backtest.acquisition import (
    acquisition_dispatch_payload,
)
from future_opportunity.backtest.acquisition_composition import (
    compose_historical_acquisition,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquisition-id", required=True)
    parser.add_argument("--planner-campaign-prefix", required=True)
    parser.add_argument("--funding-start-date")
    parser.add_argument("--funding-end-date")
    parser.add_argument("--funding-sample", type=Path)
    parser.add_argument("--cash-case-plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-total-items", type=int, default=31)
    args = parser.parse_args()

    funding_sample = (
        json.loads(args.funding_sample.read_text())
        if args.funding_sample is not None
        else None
    )
    cash_plan = (
        json.loads(args.cash_case_plan.read_text())
        if args.cash_case_plan is not None
        else None
    )
    manifest = compose_historical_acquisition(
        acquisition_id=args.acquisition_id,
        planner_campaign_prefix=args.planner_campaign_prefix,
        funding_start_date=args.funding_start_date,
        funding_end_date=args.funding_end_date,
        funding_sample=funding_sample,
        cash_case_plan=cash_plan,
        max_total_items=args.max_total_items,
    )
    payload = acquisition_dispatch_payload(manifest)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
