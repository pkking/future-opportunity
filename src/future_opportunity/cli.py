from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import AsyncIterator
from decimal import Decimal, InvalidOperation

import typer

from future_opportunity.adapters.exchanges.factory import (
    cash_and_carry_market_data_for,
    funding_market_data_for,
)
from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.manage.cash_and_carry import RefreshCashAndCarry
from future_opportunity.application.manage.close_cash_and_carry import CloseCashAndCarry
from future_opportunity.application.manage.close_funding_carry import CloseFundingCarry
from future_opportunity.application.manage.funding_carry import RefreshFundingCarry
from future_opportunity.application.repositories import (
    OpportunityRepository,
    SimulationRepository,
)
from future_opportunity.application.simulate.cash_and_carry import (
    FutureInstrumentNotFound,
    SimulateCashAndCarry,
)
from future_opportunity.application.simulate.errors import OpportunityNotQualified
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.definition import STRATEGIES
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


app = typer.Typer(help="Market-neutral arbitrage workbench")


@asynccontextmanager
async def _cli_repositories() -> AsyncIterator[
    tuple[OpportunityRepository, SimulationRepository]
]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        yield MemoryOpportunityRepository(), MemorySimulationRepository()
        return

    from future_opportunity.adapters.persistence.postgres import (
        PostgresOpportunityRepository,
        PostgresSimulationRepository,
    )

    opportunities = await PostgresOpportunityRepository.connect(database_url)
    simulations = await PostgresSimulationRepository.connect(database_url)
    try:
        yield opportunities, simulations
    finally:
        await opportunities.close()
        await simulations.close()


@app.command()
def version() -> None:
    """Print the CLI version."""
    typer.echo("future-opportunity 0.1.0")


def _decimal_cli(name: str, value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise typer.BadParameter(
            f"{name} must be a decimal number, got: {value!r}"
        ) from error


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
def strategies() -> None:
    """List supported versioned arbitrage strategies."""
    typer.echo([asdict(definition) for definition in STRATEGIES.values()])


@app.command()
def discover(
    strategy: str,
    base: str = "BTC",
    venue: str = "binance",
    capital: str = "10000",
    spot_fee_bps: str = "10",
    derivative_fee_bps: str = "5",
    reserve_ratio: str = "0.10",
    futures_leverage: str = "1",
    exit_buffer_bps: str = "5",
) -> None:
    """Discover opportunities using professional strategy semantics."""
    capital_value = _decimal_cli("capital", capital)
    spot_fee_value = _decimal_cli("spot_fee_bps", spot_fee_bps)
    derivative_fee_value = _decimal_cli(
        "derivative_fee_bps",
        derivative_fee_bps,
    )
    reserve_value = _decimal_cli("reserve_ratio", reserve_ratio)
    leverage_value = _decimal_cli("futures_leverage", futures_leverage)
    exit_buffer_value = _decimal_cli("exit_buffer_bps", exit_buffer_bps)

    async def run() -> None:
        async with _cli_repositories() as (repository, _):
            if strategy == "funding-carry":
                result = await DiscoverFundingCarry(
                    funding_market_data_for(venue),
                    repository,
                ).execute(
                    base=base,
                    capital=capital_value,
                    assumptions=_funding_assumptions(
                        spot_fee_value,
                        derivative_fee_value,
                        reserve_value,
                        leverage_value,
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
                    capital=capital_value,
                    assumptions=_cash_assumptions(
                        spot_fee_value,
                        derivative_fee_value,
                        reserve_value,
                        leverage_value,
                        exit_buffer_value,
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
    capital: str = "1000",
    spot_fee_bps: str = "10",
    derivative_fee_bps: str = "5",
    reserve_ratio: str = "0.10",
    futures_leverage: str = "1",
    exit_buffer_bps: str = "5",
    future_instrument_id: str | None = None,
) -> None:
    """Paper-execute a strategy from the exact observed Opportunity."""
    capital_value = _decimal_cli("capital", capital)
    spot_fee_value = _decimal_cli("spot_fee_bps", spot_fee_bps)
    derivative_fee_value = _decimal_cli(
        "derivative_fee_bps",
        derivative_fee_bps,
    )
    reserve_value = _decimal_cli("reserve_ratio", reserve_ratio)
    leverage_value = _decimal_cli("futures_leverage", futures_leverage)
    exit_buffer_value = _decimal_cli("exit_buffer_bps", exit_buffer_bps)

    async def run() -> None:
        async with _cli_repositories() as (repository, simulations):
            if strategy == "funding-carry":
                try:
                    simulated = await SimulateFundingCarry(
                        DiscoverFundingCarry(
                            funding_market_data_for(venue),
                            repository,
                        ),
                        simulations,
                    ).execute(
                        base=base,
                        capital=capital_value,
                        assumptions=_funding_assumptions(
                            spot_fee_value,
                            derivative_fee_value,
                            reserve_value,
                            leverage_value,
                        ),
                    )
                except OpportunityNotQualified as error:
                    raise typer.BadParameter(str(error)) from error
                typer.echo(
                    {
                        "mode": "paper",
                        "live_orders": False,
                        "observation_id": simulated.discovered.observation.id,
                        "plan": asdict(simulated.plan),
                        "position": asdict(simulated.execution.position),
                        "fills": [asdict(fill) for fill in simulated.execution.fills],
                        "return_attribution": asdict(simulated.execution.entry_return),
                        "risk": asdict(simulated.risk),
                    }
                )
                return

            if strategy == "cash-and-carry":
                if future_instrument_id is None:
                    raise typer.BadParameter(
                        "--future-instrument-id is required for cash-and-carry simulation"
                    )

                try:
                    simulated = await SimulateCashAndCarry(
                        DiscoverCashAndCarry(
                            cash_and_carry_market_data_for(venue),
                            repository,
                        ),
                        simulations,
                    ).execute(
                        base=base,
                        future_instrument_id=future_instrument_id,
                        capital=capital_value,
                        assumptions=_cash_assumptions(
                            spot_fee_value,
                            derivative_fee_value,
                            reserve_value,
                            leverage_value,
                            exit_buffer_value,
                        ),
                    )
                except FutureInstrumentNotFound as error:
                    raise typer.BadParameter(
                        f"future instrument not found: {error}"
                    ) from error
                except OpportunityNotQualified as error:
                    raise typer.BadParameter(str(error)) from error

                typer.echo(
                    {
                        "mode": "paper",
                        "live_orders": False,
                        "observation_id": simulated.discovered.observation.id,
                        "plan": asdict(simulated.plan),
                        "position": asdict(simulated.execution.position),
                        "fills": [asdict(fill) for fill in simulated.execution.fills],
                        "return_attribution": asdict(simulated.execution.entry_return),
                        "risk": asdict(simulated.risk),
                    }
                )
                return

            raise typer.BadParameter(f"unsupported strategy: {strategy}")

    asyncio.run(run())


@app.command()
def quickstart(
    strategy: str = typer.Argument("funding-carry"),
) -> None:
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


def _require_database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise typer.BadParameter(
            "DATABASE_URL is required for cross-process position management"
        )
    return value


def _position_view(record: object) -> dict[str, object]:
    return {
        "position": asdict(record.position),
        "plan": asdict(record.plan),
        "current_return": asdict(record.current_return),
        "current_net_pnl": record.current_return.net_pnl,
        "return_complete": record.current_return.complete,
        "risk": asdict(record.risk),
        "management_executions": [
            asdict(execution) for execution in record.management_executions
        ],
    }


@app.command("positions")
def list_positions() -> None:
    """List persisted paper positions. Requires DATABASE_URL."""

    async def run() -> None:
        from future_opportunity.adapters.persistence.postgres import (
            PostgresSimulationRepository,
        )

        repository = await PostgresSimulationRepository.connect(
            _require_database_url()
        )
        try:
            records = await repository.list()
            typer.echo([_position_view(record) for record in records])
        finally:
            await repository.close()

    asyncio.run(run())


@app.command("position-show")
def position_show(position_id: str) -> None:
    """Inspect one persisted paper position."""

    async def run() -> None:
        from future_opportunity.adapters.persistence.postgres import (
            PostgresSimulationRepository,
        )

        repository = await PostgresSimulationRepository.connect(
            _require_database_url()
        )
        try:
            record = await repository.get(position_id)
            if record is None:
                raise typer.BadParameter(f"position not found: {position_id}")
            typer.echo(_position_view(record))
        finally:
            await repository.close()

    asyncio.run(run())


@app.command("position-refresh")
def position_refresh(position_id: str) -> None:
    """Refresh current return and risk from live public market data."""

    async def run() -> None:
        from future_opportunity.adapters.persistence.postgres import (
            PostgresSimulationRepository,
        )

        repository = await PostgresSimulationRepository.connect(
            _require_database_url()
        )
        try:
            record = await repository.get(position_id)
            if record is None:
                raise typer.BadParameter(f"position not found: {position_id}")

            if record.plan.strategy.name == "funding-carry":
                refreshed = await RefreshFundingCarry(
                    funding_market_data_for(record.plan.venue),
                    repository,
                ).execute(position_id)
            elif record.plan.strategy.name == "cash-and-carry":
                refreshed = await RefreshCashAndCarry(
                    cash_and_carry_market_data_for(record.plan.venue),
                    repository,
                ).execute(position_id)
            else:
                raise typer.BadParameter(
                    f"unsupported strategy: {record.plan.strategy.name}"
                )
            typer.echo(_position_view(refreshed))
        finally:
            await repository.close()

    asyncio.run(run())


@app.command("position-close")
def position_close(position_id: str) -> None:
    """Paper-close a position and persist immutable exit-fill evidence."""

    async def run() -> None:
        from future_opportunity.adapters.persistence.postgres import (
            PostgresSimulationRepository,
        )

        repository = await PostgresSimulationRepository.connect(
            _require_database_url()
        )
        try:
            record = await repository.get(position_id)
            if record is None:
                raise typer.BadParameter(f"position not found: {position_id}")

            if record.plan.strategy.name == "funding-carry":
                closed = await CloseFundingCarry(
                    funding_market_data_for(record.plan.venue),
                    repository,
                ).execute(position_id)
            elif record.plan.strategy.name == "cash-and-carry":
                closed = await CloseCashAndCarry(
                    cash_and_carry_market_data_for(record.plan.venue),
                    repository,
                ).execute(position_id)
            else:
                raise typer.BadParameter(
                    f"unsupported strategy: {record.plan.strategy.name}"
                )
            typer.echo(_position_view(closed))
        finally:
            await repository.close()

    asyncio.run(run())


@app.command("opportunity-show")
def opportunity_show(opportunity_id: str) -> None:
    """Inspect one persisted Opportunity and its latest observation."""

    async def run() -> None:
        from future_opportunity.adapters.persistence.postgres import (
            PostgresOpportunityRepository,
        )

        repository = await PostgresOpportunityRepository.connect(
            _require_database_url()
        )
        try:
            opportunity = await repository.get(opportunity_id)
            if opportunity is None:
                raise typer.BadParameter(
                    f"opportunity not found: {opportunity_id}"
                )
            observations = await repository.observations(opportunity_id)
            typer.echo(
                {
                    "opportunity": asdict(opportunity),
                    "observation_count": len(observations),
                    "latest_observation": (
                        asdict(observations[-1]) if observations else None
                    ),
                }
            )
        finally:
            await repository.close()

    asyncio.run(run())


@app.command("opportunity-history")
def opportunity_history(opportunity_id: str) -> None:
    """Show immutable observations for one persisted Opportunity."""

    async def run() -> None:
        from future_opportunity.adapters.persistence.postgres import (
            PostgresOpportunityRepository,
        )

        repository = await PostgresOpportunityRepository.connect(
            _require_database_url()
        )
        try:
            opportunity = await repository.get(opportunity_id)
            if opportunity is None:
                raise typer.BadParameter(
                    f"opportunity not found: {opportunity_id}"
                )
            observations = await repository.observations(opportunity_id)
            typer.echo([asdict(observation) for observation in observations])
        finally:
            await repository.close()

    asyncio.run(run())


@app.command("db-migrate")
def db_migrate() -> None:
    """Apply pending PostgreSQL migrations with checksum verification."""
    from future_opportunity.adapters.persistence.migrations import apply_migrations

    applied = apply_migrations(_require_database_url())
    typer.echo(
        {
            "applied": [migration.name for migration in applied],
            "count": len(applied),
        }
    )
