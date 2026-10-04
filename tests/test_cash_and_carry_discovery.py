from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.adapters.persistence.memory import MemoryOpportunityRepository
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.opportunity.model import OpportunityState
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions


class FakeCashAndCarryMarketData:
    def __init__(self, future_bid: Decimal) -> None:
        self.future_bid = future_bid

    async def snapshots(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[CashAndCarryMarketSnapshot, ...]:
        now = datetime.now(UTC)
        spot = OrderBook(
            bids=(OrderBookLevel(price=Decimal(99), quantity=Decimal(100)),),
            asks=(OrderBookLevel(price=Decimal(100), quantity=Decimal(100)),),
            observed_at=now,
        )
        future = OrderBook(
            bids=(OrderBookLevel(price=self.future_bid, quantity=Decimal(100)),),
            asks=(OrderBookLevel(price=self.future_bid + Decimal(1), quantity=Decimal(100)),),
            observed_at=now,
        )
        return (
            CashAndCarryMarketSnapshot(
                venue="fake",
                base=base,
                quote=quote,
                spot_instrument_id=f"fake:{base}-{quote}:spot",
                future_instrument_id=f"fake:{base}-{quote}-future:future",
                spot_book=spot,
                future_book=future,
                expiry=now + timedelta(days=90),
                observed_at=now,
            ),
        )


@pytest.mark.asyncio
async def test_positive_net_contango_is_qualified() -> None:
    results = await DiscoverCashAndCarry(
        FakeCashAndCarryMarketData(Decimal(103)),
        MemoryOpportunityRepository(),
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=CashAndCarryAssumptions(),
    )

    result = results[0]
    assert result.qualification.qualified is True
    assert result.opportunity.state is OpportunityState.QUALIFIED


@pytest.mark.asyncio
async def test_backwardation_is_not_qualified() -> None:
    results = await DiscoverCashAndCarry(
        FakeCashAndCarryMarketData(Decimal(98)),
        MemoryOpportunityRepository(),
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=CashAndCarryAssumptions(),
    )

    result = results[0]
    assert result.qualification.qualified is False
    assert "future_not_in_contango" in result.qualification.reasons
    assert result.opportunity.state is OpportunityState.DISCOVERED
