from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.api import _history_record_view
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.manage.close_cash_and_carry import CloseCashAndCarry
from future_opportunity.application.manage.close_funding_carry import CloseFundingCarry
from future_opportunity.application.simulate.cash_and_carry import SimulateCashAndCarry
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
from future_opportunity.domain.execution.model import ExecutionPurpose
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


class FundingData:
    async def snapshot(self, base: str, quote: str = "USDT") -> FundingCarryMarketSnapshot:
        now = datetime.now(UTC)
        return FundingCarryMarketSnapshot(
            venue="fake",
            base=base,
            quote=quote,
            spot_instrument_id="fake:spot",
            perpetual_instrument_id="fake:perp",
            spot_book=book(Decimal("100.5"), Decimal(101)),
            perpetual_book=book(Decimal("101.2"), Decimal("101.7")),
            mark_price=Decimal("101.45"),
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


class CashData:
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
                spot_book=book(Decimal("100.5"), Decimal(101)),
                future_book=book(Decimal("101.5"), Decimal(102)),
                expiry=now + timedelta(days=90),
                observed_at=now,
            ),
        )


@pytest.mark.asyncio
async def test_funding_close_preserves_exit_evidence_and_partial_return() -> None:
    opportunities = MemoryOpportunityRepository()
    simulations = MemorySimulationRepository()
    market = FundingData()

    simulated = await SimulateFundingCarry(
        DiscoverFundingCarry(market, opportunities),
        simulations,
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    closed = await CloseFundingCarry(market, simulations).execute(
        simulated.execution.position.id
    )

    assert closed.position.state is PositionState.CLOSED
    assert closed.position.legs == ()
    assert closed.position.delta_pct == Decimal(0)
    assert closed.current_return.complete is False
    assert closed.current_return.unassessed_components == ("funding",)
    assert len(closed.management_executions) == 1

    close_execution = closed.management_executions[0]
    assert close_execution.purpose is ExecutionPurpose.CLOSE
    assert {fill.side for fill in close_execution.fills} == {"buy", "sell"}

    history = _history_record_view(closed)
    assert history["progress_state"] == "realized_partial"


@pytest.mark.asyncio
async def test_cash_close_is_complete_realized_paper_return() -> None:
    opportunities = MemoryOpportunityRepository()
    simulations = MemorySimulationRepository()
    market = CashData()

    simulated = await SimulateCashAndCarry(
        DiscoverCashAndCarry(market, opportunities),
        simulations,
    ).execute(
        base="BTC",
        future_instrument_id="fake:future",
        capital=Decimal(10_000),
        assumptions=CashAndCarryAssumptions(),
    )

    closed = await CloseCashAndCarry(market, simulations).execute(
        simulated.execution.position.id
    )

    assert closed.position.state is PositionState.CLOSED
    assert closed.position.legs == ()
    assert closed.current_return.complete is True
    assert len(closed.management_executions) == 1
    assert closed.management_executions[0].purpose is ExecutionPurpose.CLOSE

    history = _history_record_view(closed)
    assert history["progress_state"] == "realized"
    assert history["current"]["complete"] is True
