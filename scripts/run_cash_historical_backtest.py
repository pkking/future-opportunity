from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal
from pathlib import Path

from future_opportunity.application.backtest.cash_and_carry import (
    run_cash_and_carry_backtest,
)
from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.backtest.evidence import write_backtest_evidence
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/cash-historical-backtest/report.json"),
    )
    parser.add_argument("--capital", type=Decimal, default=Decimal(10_000))
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    case = load_cash_and_carry_close_fixture(args.fixture)
    report = await run_cash_and_carry_backtest(
        (case,),
        capital=args.capital,
        assumptions=CashAndCarryAssumptions(),
    )
    write_backtest_evidence(
        {
            "schema_version": 1,
            "evidence_type": "historical_backtest_actuals",
            "target_status": "not_yet_decided",
            "dataset_id": case.case_id,
            "backtest": report,
        },
        args.output,
    )


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
