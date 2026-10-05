from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal
from pathlib import Path

from future_opportunity.application.backtest.funding_carry import (
    run_funding_carry_backtest,
)
from future_opportunity.backtest.evidence import write_backtest_evidence
from future_opportunity.backtest.fixture import (
    build_funding_case,
    load_funding_history_fixture,
)
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/historical-backtest/report.json"),
    )
    parser.add_argument("--capital", type=Decimal, default=Decimal(10_000))
    parser.add_argument("--horizon-days", type=int, default=1)
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    fixture = load_funding_history_fixture(args.fixture)
    if len(fixture.alignment.samples) < 2:
        raise RuntimeError("historical fixture has fewer than two aligned books")

    historical_case = build_funding_case(
        fixture,
        entry_index=0,
        exit_index=len(fixture.alignment.samples) - 1,
    )
    report = await run_funding_carry_backtest(
        (historical_case,),
        capital=args.capital,
        assumptions=FundingCarryAssumptions(
            horizon_days=args.horizon_days,
        ),
    )
    evidence = {
        "schema_version": 1,
        "evidence_type": "historical_backtest_actuals",
        "target_status": "not_yet_decided",
        "dataset_id": fixture.dataset_id,
        "dataset_manifest": fixture.manifest,
        "alignment": fixture.alignment,
        "backtest": report,
    }
    write_backtest_evidence(evidence, args.output)


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
