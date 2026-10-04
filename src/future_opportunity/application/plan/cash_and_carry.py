from __future__ import annotations

from decimal import Decimal

from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot
from future_opportunity.domain.strategy.definition import CASH_AND_CARRY
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
    cash_and_carry_allocation,
)
from future_opportunity.domain.strategy.model import Money, PlanLeg, StrategyPlan, StrategyRef


def build_cash_and_carry_plan(
    plan_id: str,
    opportunity_observation_id: str,
    snapshot: CashAndCarryMarketSnapshot,
    capital: Decimal,
    assumptions: CashAndCarryAssumptions,
    max_delta_pct: Decimal = Decimal("0.005"),
    max_leverage: Decimal = Decimal("1.2"),
) -> StrategyPlan:
    if assumptions.futures_leverage > max_leverage:
        raise ValueError("configured futures leverage exceeds plan risk limit")

    allocation = cash_and_carry_allocation(snapshot, capital, assumptions)

    return StrategyPlan(
        id=plan_id,
        strategy=StrategyRef(name=CASH_AND_CARRY.name, version=CASH_AND_CARRY.version),
        opportunity_observation_id=opportunity_observation_id,
        capital=Money(amount=capital, currency=snapshot.quote),
        legs=(
            PlanLeg(
                id="spot-leg",
                instrument_id=snapshot.spot_instrument_id,
                side="buy",
                target_notional=Money(
                    amount=allocation.spot_notional,
                    currency=snapshot.quote,
                ),
            ),
            PlanLeg(
                id="future-leg",
                instrument_id=snapshot.future_instrument_id,
                side="sell",
                target_notional=Money(
                    amount=allocation.hedge_notional,
                    currency=snapshot.quote,
                ),
            ),
        ),
        max_delta_pct=max_delta_pct,
        max_leverage=max_leverage,
        execution_mode="paper",
    )
