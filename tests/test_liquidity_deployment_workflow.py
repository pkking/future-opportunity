from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.simulate.errors import OpportunityNotQualified
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
from future_opportunity.domain.deployment.model import LiquidityPolicy
from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


class ThinFundingMarket:
    async def snapshot(
        self,
        base: str,
        quote: str = "USDT",
    ) -> FundingCarryMarketSnapshot:
        now = datetime.now(UTC)
        spot = OrderBook(
            bids=(OrderBookLevel(price=Decimal("99.9"), quantity=Decimal(10)),),
            asks=(OrderBookLevel(price=Decimal(100), quantity=Decimal(10)),),
            observed_at=now,
        )
        perpetual = OrderBook(
            bids=(OrderBookLevel(price=Decimal(100), quantity=Decimal(10)),),
            asks=(OrderBookLevel(price=Decimal("100.1"), quantity=Decimal(10)),),
            observed_at=now,
        )
        return FundingCarryMarketSnapshot(
            venue="fixture",
            base=base,
            quote=quote,
            spot_instrument_id="fixture:spot",
            perpetual_instrument_id="fixture:perp",
            spot_book=spot,
            perpetual_book=perpetual,
            mark_price=Decimal("100.05"),
            last_funding_rate=Decimal("0.001"),
            next_funding_time=now + timedelta(hours=8),
            funding_history=tuple(
                FundingObservation(
                    rate=Decimal("0.001"),
                    funding_time=now - timedelta(hours=8 * index),
                )
                for index in range(90)
            ),
            observed_at=now,
        )


ASSUMPTIONS = FundingCarryAssumptions(
    spot_taker_fee_bps=Decimal(0),
    perpetual_taker_fee_bps=Decimal(0),
)


@pytest.mark.asyncio
async def test_strict_liquidity_policy_rejects_oversized_capital_intent() -> None:
    discovered = await DiscoverFundingCarry(
        ThinFundingMarket(),
        MemoryOpportunityRepository(),
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=ASSUMPTIONS,
        liquidity_policy=LiquidityPolicy.STRICT,
        max_impact_bps=Decimal(10),
    )

    assert discovered.qualification.qualified is False
    assert (
        "requested_notional_exceeds_liquidity_limit"
        in discovered.qualification.reasons
    )
    assert discovered.deployment.requested_spot_notional == Decimal(4_500)
    assert discovered.deployment.capacity_spot_notional == Decimal(1_000)
    assert discovered.deployment.actual_spot_notional == Decimal(0)


@pytest.mark.asyncio
async def test_strict_liquidity_policy_cannot_create_position() -> None:
    simulations = MemorySimulationRepository()

    with pytest.raises(
        OpportunityNotQualified,
        match="requested_notional_exceeds_liquidity_limit",
    ):
        await SimulateFundingCarry(
            DiscoverFundingCarry(
                ThinFundingMarket(),
                MemoryOpportunityRepository(),
            ),
            simulations,
        ).execute(
            base="BTC",
            capital=Decimal(10_000),
            assumptions=ASSUMPTIONS,
        )

    assert await simulations.list() == ()


@pytest.mark.asyncio
async def test_partial_liquidity_policy_freezes_and_executes_capacity_limited_plan() -> None:
    simulations = MemorySimulationRepository()
    simulated = await SimulateFundingCarry(
        DiscoverFundingCarry(
            ThinFundingMarket(),
            MemoryOpportunityRepository(),
        ),
        simulations,
    ).execute(
        base="BTC",
        capital=Decimal(10_000),
        assumptions=ASSUMPTIONS,
        liquidity_policy=LiquidityPolicy.PARTIAL,
        max_impact_bps=Decimal(10),
    )

    deployment = simulated.plan.deployment
    assert deployment is not None
    assert deployment.policy is LiquidityPolicy.PARTIAL
    assert deployment.partial_deployment is True
    assert deployment.requested_spot_notional == Decimal(4_500)
    assert deployment.capacity_spot_notional == Decimal(1_000)
    assert deployment.actual_spot_notional == Decimal(1_000)
    assert deployment.actual_hedge_notional == Decimal(1_000)
    assert deployment.reserve_amount == Decimal(1_000)
    assert deployment.unused_capital == Decimal(7_000)

    assert simulated.plan.legs[0].target_notional.amount == Decimal(1_000)
    assert simulated.plan.legs[1].target_notional.amount == Decimal(1_000)
    assert all(
        fill.slippage_bps <= deployment.max_impact_bps
        for fill in simulated.execution.fills
    )
    assert simulated.plan.expected_economics is not None
    assert simulated.plan.expected_economics.expected_net_return > Decimal(0)
