from __future__ import annotations

import argparse

from future_opportunity.backtest.date_range import historical_date_range_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("start_date")
    parser.add_argument("end_date")
    parser.add_argument("--max-days", type=int, default=31)
    args = parser.parse_args()

    print(
        historical_date_range_json(
            args.start_date,
            args.end_date,
            max_days=args.max_days,
        )
    )


if __name__ == "__main__":
    main()
