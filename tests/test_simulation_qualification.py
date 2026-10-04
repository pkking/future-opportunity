from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.simulate.cash_and_carry import SimulateCashAndCarry
from future_opportunity.application.simulate.errors import OpportunityNotQualified
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


def flat_book(bid: Decimal, ask: Decimal) -> OrderBook:
    now = datetime.now(UTC)
    return OrderBook(
        bids=(OrderBookLevel(price=bid, quantity=Decimal(100)),),
        asks=(OrderBookLevel(price=ask, quantity=Decimal(100)),),
        observed_at=now,
    )


class NegativeFundingData:
    async def snapshot(
        self,
        base: str,
        quote: str = "USDT",
    ) -> FundingCarryMarketSnapshot:
        now = datetime.now(UTC)
        spot = flat_book(Decimal(99), Decimal(100))
        perpetual = flat_book(Decimal(100), Decimal(101))
        return FundingCarryMarketSnapshot(
            venue="fake",
            base=base,
            quote=quote,
            spot_instrument_id="fake:spot",
            perpetual_instrument_id="fake:perp",
            spot_book=spot,
            perpetual_book=perpetual,
            mark_price=Decimal("100.5"),
            last_funding_rate=Decimal("-0.0001"),
            next_funding_time=now + timedelta(hours=8),
            funding_history=tuple(
                FundingObservation(
                    rate=Decimal("-0.0001"),
                    funding_time=now - timedelta(hours=8 * index),
                )
                for index in range(90)
            ),
            observed_at=now,
        )


class BackwardationData:
    async def snapshots(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[CashAndCarryMarketSnapshot, ...]:
        now = datetime.now(UTC)
        return (
            CashAndCarryMarketSnapshot(
                venue="fake",
                base=base,
                quote=quote,
                spot_instrument_id="fake:spot",
                future_instrument_id="fake:future",
                spot_book=flat_book(Decimal(99), Decimal(100)),
                future_book=flat_book(Decimal(98), Decimal(99)),
                expiry=now + timedelta(days=90),
                observed_at=now,
            ),
        )


@pytest.mark.asyncio
async def test_unqualified_funding_opportunity_cannot_create_position() -> None:
    opportunities = MemoryOpportunityRepository()
    simulations = MemorySimulationRepository()

    with pytest.raises(
        OpportunityNotQualified,
        match="expected_funding_not_positive",
    ):
        await SimulateFundingCarry(
            DiscoverFundingCarry(NegativeFundingData(), opportunities),
            simulations,
        ).execute(
            base="BTC",
            capital=Decimal(10_000),
            assumptions=FundingCarryAssumptions(),
        )

    assert await simulations.list() == ()


@pytest.mark.asyncio
async def test_unqualified_cash_opportunity_cannot_create_position() -> None:
    opportunities = MemoryOpportunityRepository()
    simulations = MemorySimulationRepository()

    with pytest.raises(
        OpportunityNotQualified,
        match="future_not_in_contango",
    ):
        await SimulateCashAndCarry(
            DiscoverCashAndCarry(BackwardationData(), opportunities),
            simulations,
        ).execute(
            base="BTC",
            future_instrument_id="fake:future",
            capital=Decimal(10_000),
            assumptions=CashAndCarryAssumptions(),
        )

    assert await simulations.list() == ()
