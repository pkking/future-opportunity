from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.manage.cash_and_carry import RefreshCashAndCarry
from future_opportunity.application.manage.funding_carry import RefreshFundingCarry
from future_opportunity.application.simulate.cash_and_carry import SimulateCashAndCarry
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.position.model import PositionState
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


def book(bid: Decimal, ask: Decimal) -> OrderBook:
    now = datetime.now(UTC)
    return OrderBook(
        bids=(OrderBookLevel(price=bid, quantity=Decimal(100)),),
        asks=(OrderBookLevel(price=ask, quantity=Decimal(100)),),
        observed_at=now,
    )


class DynamicFundingData:
    def __init__(self) -> None:
        self.spot_bid = Decimal(99)
        self.spot_ask = Decimal(100)
        self.perp_bid = Decimal(101)
        self.perp_ask = Decimal(102)

    async def snapshot(self, base: str, quote: str = "USDT") -> FundingCarryMarketSnapshot:
        now = datetime.now(UTC)
        return FundingCarryMarketSnapshot(
            venue="fake",
            base=base,
            quote=quote,
            spot_instrument_id="fake:spot",
            perpetual_instrument_id="fake:perp",
            spot_book=book(self.spot_bid, self.spot_ask),
            perpetual_book=book(self.perp_bid, self.perp_ask),
            mark_price=(self.perp_bid + self.perp_ask) / Decimal(2),
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


class DynamicCashData:
    def __init__(self) -> None:
        self.spot_bid = Decimal(99)
        self.spot_ask = Decimal(100)
        self.future_bid = Decimal(103)
        self.future_ask = Decimal(104)

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
                spot_book=book(self.spot_bid, self.spot_ask),
                future_book=book(self.future_bid, self.future_ask),
                expiry=now + timedelta(days=90),
                observed_at=now,
            ),
        )


@pytest.mark.asyncio
async def test_funding_refresh_marks_unknown_funding_component_unassessed() -> None:
    market = DynamicFundingData()
    simulations = MemorySimulationRepository()

    simulated = await SimulateFundingCarry(
        DiscoverFundingCarry(market, MemoryOpportunityRepository()),
        simulations,
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    market.spot_bid = Decimal("100.5")
    market.spot_ask = Decimal("101")
    market.perp_bid = Decimal("101.2")
    market.perp_ask = Decimal("101.7")

    refreshed = await RefreshFundingCarry(market, simulations).execute(
        simulated.execution.position.id
    )

    assert refreshed.position.state is PositionState.ACTIVE
    assert refreshed.position.version == 1
    assert refreshed.current_return.complete is False
    assert refreshed.current_return.unassessed_components == ("funding",)


@pytest.mark.asyncio
async def test_cash_refresh_produces_complete_closeable_return() -> None:
    market = DynamicCashData()
    simulations = MemorySimulationRepository()

    simulated = await SimulateCashAndCarry(
        DiscoverCashAndCarry(market, MemoryOpportunityRepository()),
        simulations,
    ).execute(
        base="BTC",
        future_instrument_id="fake:future",
        capital=Decimal(10_000),
        assumptions=CashAndCarryAssumptions(),
    )

    market.spot_bid = Decimal("100.5")
    market.spot_ask = Decimal("101")
    market.future_bid = Decimal("101.5")
    market.future_ask = Decimal("102")

    refreshed = await RefreshCashAndCarry(market, simulations).execute(
        simulated.execution.position.id
    )

    assert refreshed.position.state is PositionState.ACTIVE
    assert refreshed.position.version == 1
    assert refreshed.current_return.complete is True
    assert refreshed.current_return.unassessed_components == ()
    assert refreshed.current_return.basis_convergence > Decimal(0)
