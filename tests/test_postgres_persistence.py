from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import os

import psycopg
import pytest

from future_opportunity.adapters.persistence.postgres import (
    PostgresOpportunityRepository,
    PostgresSimulationRepository,
)
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


class FundingData:
    async def snapshot(self, base: str, quote: str = "USDT") -> FundingCarryMarketSnapshot:
        now = datetime.now(UTC)
        spot = OrderBook(
            bids=(OrderBookLevel(Decimal(99), Decimal(100)),),
            asks=(OrderBookLevel(Decimal(100), Decimal(100)),),
            observed_at=now,
        )
        perpetual = OrderBook(
            bids=(OrderBookLevel(Decimal(101), Decimal(100)),),
            asks=(OrderBookLevel(Decimal(102), Decimal(100)),),
            observed_at=now,
        )
        return FundingCarryMarketSnapshot(
            venue="integration",
            base=base,
            quote=quote,
            spot_instrument_id="integration:spot",
            perpetual_instrument_id="integration:perp",
            spot_book=spot,
            perpetual_book=perpetual,
            mark_price=Decimal("101.5"),
            last_funding_rate=Decimal("0.0002"),
            next_funding_time=now + timedelta(hours=8),
            funding_history=tuple(
                FundingObservation(
                    rate=Decimal("0.0002"),
                    funding_time=now - timedelta(hours=8 * index),
                )
                for index in range(90)
            ),
            observed_at=now,
        )


def apply_migrations(dsn: str) -> None:
    with psycopg.connect(dsn, autocommit=True) as connection:
        for path in sorted(Path("migrations").glob("*.sql")):
            connection.execute(path.read_text())


@pytest.mark.asyncio
@pytest.mark.skipif(TEST_DATABASE_URL is None, reason="TEST_DATABASE_URL is not set")
async def test_postgres_round_trip_rebuilds_complete_simulation() -> None:
    assert TEST_DATABASE_URL is not None
    apply_migrations(TEST_DATABASE_URL)

    opportunities = await PostgresOpportunityRepository.connect(TEST_DATABASE_URL)
    simulations = await PostgresSimulationRepository.connect(TEST_DATABASE_URL)

    try:
        simulated = await SimulateFundingCarry(
            DiscoverFundingCarry(FundingData(), opportunities),
            simulations,
        ).execute(
            base="BTC",
            capital=Decimal(10_000),
            assumptions=FundingCarryAssumptions(),
        )

        stored = await simulations.get(simulated.execution.position.id)

        assert stored is not None
        assert stored.plan.id == simulated.plan.id
        assert stored.plan.opportunity_observation_id == simulated.discovered.observation.id
        assert stored.plan.expected_economics is not None
        assert simulated.plan.expected_economics is not None
        assert (
            stored.plan.expected_economics.expected_net_pnl
            == simulated.plan.expected_economics.expected_net_pnl
        )
        assert stored.execution.id == simulated.execution_record.id
        assert len(stored.execution.fills) == 2
        assert stored.position.id == simulated.execution.position.id
        assert stored.entry_return.net_pnl == simulated.execution.entry_return.net_pnl
        assert stored.current_return.net_pnl == stored.entry_return.net_pnl
        assert len(stored.risk.invariants) == 6

        listed = await simulations.list()
        assert [record.position.id for record in listed] == [stored.position.id]
    finally:
        await opportunities.close()
        await simulations.close()
