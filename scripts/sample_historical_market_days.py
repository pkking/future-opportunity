from __future__ import annotations

import argparse
from pathlib import Path

from future_opportunity.backtest.sampling import (
    HistoricalSamplingRequest,
    historical_sampling_json,
    sample_historical_market_days,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--sample-size", type=int, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument(
        "--policy-version",
        default="systematic-stratified-sha256-v1",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = sample_historical_market_days(
        HistoricalSamplingRequest(
            strategy=args.strategy,
            start_date=args.start_date,
            end_date=args.end_date,
            sample_size=args.sample_size,
            seed=args.seed,
            policy_version=args.policy_version,
        )
    )
    encoded = historical_sampling_json(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
