import asyncio
from dataclasses import asdict
from decimal import Decimal

import typer

from future_opportunity.adapters.exchanges.factory import funding_market_data_for
from future_opportunity.adapters.persistence.memory import MemoryOpportunityRepository
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.execute.paper_funding_carry import (
    execute_paper_funding_carry,
)
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


app = typer.Typer(help="Market-neutral arbitrage workbench")


@app.command()
def version() -> None:
    """Print the CLI version."""
    typer.echo("future-opportunity 0.1.0")


def _assumptions(
    spot_fee_bps: Decimal,
    perpetual_fee_bps: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
) -> FundingCarryAssumptions:
    return FundingCarryAssumptions(
        spot_taker_fee_bps=spot_fee_bps,
        perpetual_taker_fee_bps=perpetual_fee_bps,
        reserve_ratio=reserve_ratio,
        futures_leverage=futures_leverage,
    )


@app.command()
def discover(
    base: str = "BTC",
    venue: str = "binance",
    capital: Decimal = Decimal(10_000),
    spot_fee_bps: Decimal = Decimal(10),
    perpetual_fee_bps: Decimal = Decimal(5),
    reserve_ratio: Decimal = Decimal("0.10"),
    futures_leverage: Decimal = Decimal(1),
) -> None:
    """Discover a funding-carry opportunity from public market data."""

    async def run() -> None:
        use_case = DiscoverFundingCarry(
            funding_market_data_for(venue),
            MemoryOpportunityRepository(),
        )
        result = await use_case.execute(
            base=base,
            capital=capital,
            assumptions=_assumptions(
                spot_fee_bps,
                perpetual_fee_bps,
                reserve_ratio,
                futures_leverage,
            ),
        )
        typer.echo(asdict(result))

    asyncio.run(run())


@app.command()
def simulate(
    base: str = "BTC",
    venue: str = "binance",
    capital: Decimal = Decimal(1_000),
    spot_fee_bps: Decimal = Decimal(10),
    perpetual_fee_bps: Decimal = Decimal(5),
    reserve_ratio: Decimal = Decimal("0.10"),
    futures_leverage: Decimal = Decimal(1),
) -> None:
    """Paper-execute a funding-carry position against a real order book."""

    async def run() -> None:
        configured = _assumptions(
            spot_fee_bps,
            perpetual_fee_bps,
            reserve_ratio,
            futures_leverage,
        )
        snapshot = await funding_market_data_for(venue).snapshot(base)
        result = execute_paper_funding_carry(
            position_id="quickstart-position",
            strategy_plan_id="quickstart-plan",
            snapshot=snapshot,
            capital=capital,
            assumptions=configured,
        )
        risk = evaluate_delta_neutrality(
            result.position,
            max_delta_pct=Decimal("0.005"),
        )
        typer.echo(
            {
                "mode": "paper",
                "live_orders": False,
                "venue": venue,
                "position": asdict(result.position),
                "risk": asdict(risk),
            }
        )

    asyncio.run(run())


@app.command()
def quickstart(strategy: str = "funding-carry") -> None:
    """Show the safe V0 quickstart command."""
    if strategy != "funding-carry":
        raise typer.BadParameter("V0 quickstart currently supports funding-carry")
    typer.echo("Run: arb discover BTC --venue binance --capital 1000")
    typer.echo("Then: arb simulate BTC --venue binance --capital 1000")
    typer.echo("Try OKX: arb discover BTC --venue okx --capital 1000")
    typer.echo("V0 execution mode is paper; live orders are disabled.")
