from __future__ import annotations

import asyncio
from dataclasses import asdict
from decimal import Decimal
from uuid import uuid4

import typer

from future_opportunity.adapters.exchanges.factory import (
    cash_and_carry_market_data_for,
    funding_market_data_for,
)
from future_opportunity.adapters.persistence.memory import MemoryOpportunityRepository
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.execute.paper_cash_and_carry import (
    execute_paper_cash_and_carry,
)
from future_opportunity.application.execute.paper_funding_carry import (
    execute_paper_funding_carry,
)
from future_opportunity.application.plan.cash_and_carry import build_cash_and_carry_plan
from future_opportunity.application.plan.funding_carry import build_funding_carry_plan
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


app = typer.Typer(help="Market-neutral arbitrage workbench")


@app.command()
def version() -> None:
    """Print the CLI version."""
    typer.echo("future-opportunity 0.1.0")


def _funding_assumptions(
    spot_fee_bps: Decimal,
    derivative_fee_bps: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
) -> FundingCarryAssumptions:
    return FundingCarryAssumptions(
        spot_taker_fee_bps=spot_fee_bps,
        perpetual_taker_fee_bps=derivative_fee_bps,
        reserve_ratio=reserve_ratio,
        futures_leverage=futures_leverage,
    )


def _cash_assumptions(
    spot_fee_bps: Decimal,
    derivative_fee_bps: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
    exit_buffer_bps: Decimal,
) -> CashAndCarryAssumptions:
    return CashAndCarryAssumptions(
        reserve_ratio=reserve_ratio,
        futures_leverage=futures_leverage,
        spot_entry_fee_bps=spot_fee_bps,
        spot_exit_fee_bps=spot_fee_bps,
        futures_entry_fee_bps=derivative_fee_bps,
        futures_settlement_fee_bps=derivative_fee_bps,
        exit_buffer_bps=exit_buffer_bps,
    )


def _result_view(result: object) -> dict[str, object]:
    return {
        "opportunity": asdict(result.opportunity),
        "observation": asdict(result.observation),
        "qualification": asdict(result.qualification),
        "evaluation": asdict(result.evaluation),
    }


@app.command()
def discover(
    strategy: str,
    base: str = "BTC",
    venue: str = "binance",
    capital: Decimal = Decimal(10_000),
    spot_fee_bps: Decimal = Decimal(10),
    derivative_fee_bps: Decimal = Decimal(5),
    reserve_ratio: Decimal = Decimal("0.10"),
    futures_leverage: Decimal = Decimal(1),
    exit_buffer_bps: Decimal = Decimal(5),
) -> None:
    """Discover opportunities using professional strategy semantics."""

    async def run() -> None:
        repository = MemoryOpportunityRepository()

        if strategy == "funding-carry":
            result = await DiscoverFundingCarry(
                funding_market_data_for(venue),
                repository,
            ).execute(
                base=base,
                capital=capital,
                assumptions=_funding_assumptions(
                    spot_fee_bps,
                    derivative_fee_bps,
                    reserve_ratio,
                    futures_leverage,
                ),
            )
            typer.echo(_result_view(result))
            return

        if strategy == "cash-and-carry":
            results = await DiscoverCashAndCarry(
                cash_and_carry_market_data_for(venue),
                repository,
            ).execute(
                base=base,
                capital=capital,
                assumptions=_cash_assumptions(
                    spot_fee_bps,
                    derivative_fee_bps,
                    reserve_ratio,
                    futures_leverage,
                    exit_buffer_bps,
                ),
            )
            typer.echo([_result_view(result) for result in results])
            return

        raise typer.BadParameter(f"unsupported strategy: {strategy}")

    asyncio.run(run())


@app.command()
def simulate(
    strategy: str,
    base: str = "BTC",
    venue: str = "binance",
    capital: Decimal = Decimal(1_000),
    spot_fee_bps: Decimal = Decimal(10),
    derivative_fee_bps: Decimal = Decimal(5),
    reserve_ratio: Decimal = Decimal("0.10"),
    futures_leverage: Decimal = Decimal(1),
    exit_buffer_bps: Decimal = Decimal(5),
    future_instrument_id: str | None = None,
) -> None:
    """Paper-execute a strategy from the exact observed Opportunity."""

    async def run() -> None:
        repository = MemoryOpportunityRepository()

        if strategy == "funding-carry":
            configured = _funding_assumptions(
                spot_fee_bps,
                derivative_fee_bps,
                reserve_ratio,
                futures_leverage,
            )
            discovered = await DiscoverFundingCarry(
                funding_market_data_for(venue),
                repository,
            ).execute(
                base=base,
                capital=capital,
                assumptions=configured,
            )
            plan = build_funding_carry_plan(
                plan_id=str(uuid4()),
                opportunity_observation_id=discovered.observation.id,
                snapshot=discovered.snapshot,
                capital=capital,
                assumptions=configured,
            )
            execution = execute_paper_funding_carry(
                position_id=str(uuid4()),
                strategy_plan_id=plan.id,
                snapshot=discovered.snapshot,
                capital=capital,
                assumptions=configured,
            )
            risk = evaluate_delta_neutrality(execution.position, plan.max_delta_pct)
            typer.echo(
                {
                    "mode": "paper",
                    "live_orders": False,
                    "observation_id": discovered.observation.id,
                    "plan": asdict(plan),
                    "position": asdict(execution.position),
                    "risk": asdict(risk),
                }
            )
            return

        if strategy == "cash-and-carry":
            if future_instrument_id is None:
                raise typer.BadParameter(
                    "--future-instrument-id is required for cash-and-carry simulation"
                )

            configured = _cash_assumptions(
                spot_fee_bps,
                derivative_fee_bps,
                reserve_ratio,
                futures_leverage,
                exit_buffer_bps,
            )
            candidates = await DiscoverCashAndCarry(
                cash_and_carry_market_data_for(venue),
                repository,
            ).execute(
                base=base,
                capital=capital,
                assumptions=configured,
            )
            discovered = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate.snapshot.future_instrument_id == future_instrument_id
                ),
                None,
            )
            if discovered is None:
                raise typer.BadParameter(
                    f"future instrument not found: {future_instrument_id}"
                )

            plan = build_cash_and_carry_plan(
                plan_id=str(uuid4()),
                opportunity_observation_id=discovered.observation.id,
                snapshot=discovered.snapshot,
                capital=capital,
                assumptions=configured,
            )
            execution = execute_paper_cash_and_carry(
                position_id=str(uuid4()),
                strategy_plan_id=plan.id,
                snapshot=discovered.snapshot,
                capital=capital,
                assumptions=configured,
            )
            risk = evaluate_delta_neutrality(execution.position, plan.max_delta_pct)
            typer.echo(
                {
                    "mode": "paper",
                    "live_orders": False,
                    "observation_id": discovered.observation.id,
                    "plan": asdict(plan),
                    "position": asdict(execution.position),
                    "risk": asdict(risk),
                }
            )
            return

        raise typer.BadParameter(f"unsupported strategy: {strategy}")

    asyncio.run(run())


@app.command()
def quickstart(strategy: str = "funding-carry") -> None:
    """Show safe executable examples for the V0 paper workflow."""
    if strategy == "funding-carry":
        typer.echo("1. arb discover funding-carry --venue binance --base BTC --capital 1000")
        typer.echo("2. arb simulate funding-carry --venue binance --base BTC --capital 1000")
    elif strategy == "cash-and-carry":
        typer.echo("1. arb discover cash-and-carry --venue okx --base BTC --capital 1000")
        typer.echo("2. Copy a future_instrument_id from the candidate evaluation.")
        typer.echo(
            "3. arb simulate cash-and-carry --venue okx --base BTC "
            "--capital 1000 --future-instrument-id <id>"
        )
    else:
        raise typer.BadParameter(f"unsupported strategy: {strategy}")

    typer.echo("V0 execution mode is paper; live orders are disabled.")
