from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.opportunity.model import OpportunityState
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


class FakeFundingMarketData:
    def __init__(self, rate: Decimal) -> None:
        self._rate = rate

    async def snapshot(self, base: str, quote: str = "USDT") -> FundingCarryMarketSnapshot:
        now = datetime.now(UTC)
        book = OrderBook(
            bids=(OrderBookLevel(price=Decimal(100), quantity=Decimal(100)),),
            asks=(OrderBookLevel(price=Decimal(100), quantity=Decimal(100)),),
            observed_at=now,
        )
        history = tuple(
            FundingObservation(
                rate=self._rate,
                funding_time=now - timedelta(hours=8 * index),
            )
            for index in range(90)
        )
        return FundingCarryMarketSnapshot(
            venue="fake",
            base=base,
            quote=quote,
            spot_instrument_id=f"fake:{base}{quote}:spot",
            perpetual_instrument_id=f"fake:{base}{quote}:perpetual",
            spot_book=book,
            perpetual_book=book,
            mark_price=Decimal(100),
            last_funding_rate=self._rate,
            next_funding_time=now + timedelta(hours=8),
            funding_history=history,
            observed_at=now,
        )


@pytest.mark.asyncio
async def test_positive_net_carry_is_qualified() -> None:
    result = await DiscoverFundingCarry(
        FakeFundingMarketData(Decimal("0.0002"))
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    assert result.qualification.qualified is True
    assert result.opportunity.state is OpportunityState.QUALIFIED


@pytest.mark.asyncio
async def test_negative_funding_is_discovered_but_not_qualified() -> None:
    result = await DiscoverFundingCarry(
        FakeFundingMarketData(Decimal("-0.0001"))
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    assert result.qualification.qualified is False
    assert "expected_funding_not_positive" in result.qualification.reasons
    assert result.opportunity.state is OpportunityState.DISCOVERED
