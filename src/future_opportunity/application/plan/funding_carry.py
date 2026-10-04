from __future__ import annotations

from decimal import Decimal

from future_opportunity.domain.capital.model import allocate_isolated_hedge
from future_opportunity.domain.market.snapshot import FundingCarryMarketSnapshot
from future_opportunity.domain.strategy.definition import FUNDING_CARRY
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions
from future_opportunity.domain.strategy.model import (
    ExpectedEconomics,
    Money,
    PlanLeg,
    StrategyPlan,
    StrategyRef,
)


def build_funding_carry_plan(
    plan_id: str,
    opportunity_observation_id: str,
    snapshot: FundingCarryMarketSnapshot,
    capital: Decimal,
    assumptions: FundingCarryAssumptions,
    expected_economics: ExpectedEconomics | None = None,
    max_delta_pct: Decimal = Decimal("0.005"),
    max_leverage: Decimal = Decimal("1.2"),
) -> StrategyPlan:
    deployed_notional = allocate_isolated_hedge(
        capital,
        assumptions.reserve_ratio,
        assumptions.futures_leverage,
    ).hedged_notional

    if assumptions.futures_leverage > max_leverage:
        raise ValueError("configured futures leverage exceeds plan risk limit")

    return StrategyPlan(
        id=plan_id,
        strategy=StrategyRef(name=FUNDING_CARRY.name, version=FUNDING_CARRY.version),
        opportunity_observation_id=opportunity_observation_id,
        venue=snapshot.venue,
        base=snapshot.base,
        quote=snapshot.quote,
        capital=Money(amount=capital, currency=snapshot.quote),
        legs=(
            PlanLeg(
                id="spot-leg",
                instrument_id=snapshot.spot_instrument_id,
                side="buy",
                target_notional=Money(amount=deployed_notional, currency=snapshot.quote),
            ),
            PlanLeg(
                id="perpetual-leg",
                instrument_id=snapshot.perpetual_instrument_id,
                side="sell",
                target_notional=Money(amount=deployed_notional, currency=snapshot.quote),
            ),
        ),
        max_delta_pct=max_delta_pct,
        max_leverage=max_leverage,
        execution_mode="paper",
        expected_economics=expected_economics,
    )
