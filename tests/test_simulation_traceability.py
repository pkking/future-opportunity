from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.api import _history_record_view
from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.simulate.cash_and_carry import SimulateCashAndCarry
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
            spot_book=book(Decimal(99), Decimal(100)),
            perpetual_book=book(Decimal(101), Decimal(102)),
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
                spot_book=book(Decimal(99), Decimal(100)),
                future_book=book(Decimal(102), Decimal(103)),
                expiry=now + timedelta(days=90),
                observed_at=now,
            ),
        )


@pytest.mark.asyncio
async def test_funding_simulation_preserves_decision_evidence_chain() -> None:
    result = await SimulateFundingCarry(
        DiscoverFundingCarry(FundingData(), MemoryOpportunityRepository()),
        MemorySimulationRepository(),
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    assert result.plan.opportunity_observation_id == result.discovered.observation.id
    assert result.execution.position.strategy_plan_id == result.plan.id
    assert result.plan.expected_economics is not None
    assert (
        result.plan.expected_economics.expected_net_pnl
        == Decimal(10_000) * result.discovered.evaluation.expected_net_return_to_expiry
    )
    assert result.plan.expected_economics is not None
    assert (
        result.plan.expected_economics.expected_net_pnl
        == Decimal(10_000) * result.discovered.evaluation.expected_net_return_horizon
    )


@pytest.mark.asyncio
async def test_cash_simulation_preserves_decision_evidence_chain() -> None:
    result = await SimulateCashAndCarry(
        DiscoverCashAndCarry(CashData(), MemoryOpportunityRepository()),
        MemorySimulationRepository(),
    ).execute(
        base="BTC",
        future_instrument_id="fake:future",
        capital=Decimal(10_000),
        assumptions=CashAndCarryAssumptions(),
    )

    assert result.plan.opportunity_observation_id == result.discovered.observation.id
    assert result.execution.position.strategy_plan_id == result.plan.id


@pytest.mark.asyncio
async def test_history_does_not_call_open_position_realized() -> None:
    simulations = MemorySimulationRepository()
    result = await SimulateFundingCarry(
        DiscoverFundingCarry(FundingData(), MemoryOpportunityRepository()),
        simulations,
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    record = await simulations.get(result.execution.position.id)
    assert record is not None

    view = _history_record_view(record)
    assert view["progress_state"] == "in_progress"
    assert view["expected"]["expected_net_pnl"] == result.plan.expected_economics.expected_net_pnl
    assert view["current"]["net_pnl"] == record.current_return.net_pnl
