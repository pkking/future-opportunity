from __future__ import annotations

from decimal import Decimal

from future_opportunity.domain.deployment.model import DeploymentAssessment
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot
from future_opportunity.domain.strategy.definition import CASH_AND_CARRY
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
    cash_and_carry_allocation,
)
from future_opportunity.domain.strategy.model import (
    CapitalPolicy,
    ExecutionCostPolicy,
    ExpectedEconomics,
    Money,
    PlanLeg,
    StrategyPlan,
    StrategyRef,
)


def build_cash_and_carry_plan(
    plan_id: str,
    opportunity_observation_id: str,
    snapshot: CashAndCarryMarketSnapshot,
    capital: Decimal,
    assumptions: CashAndCarryAssumptions,
    expected_economics: ExpectedEconomics | None = None,
    deployment: DeploymentAssessment | None = None,
    max_delta_pct: Decimal = Decimal("0.005"),
    max_leverage: Decimal = Decimal("1.2"),
) -> StrategyPlan:
    if assumptions.futures_leverage > max_leverage:
        raise ValueError("configured futures leverage exceeds plan risk limit")

    allocation = cash_and_carry_allocation(snapshot, capital, assumptions)
    spot_notional = (
        deployment.actual_spot_notional
        if deployment is not None
        else allocation.spot_notional
    )
    hedge_notional = (
        deployment.actual_hedge_notional
        if deployment is not None
        else allocation.hedge_notional
    )

    return StrategyPlan(
        id=plan_id,
        strategy=StrategyRef(name=CASH_AND_CARRY.name, version=CASH_AND_CARRY.version),
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
                target_notional=Money(
                    amount=spot_notional,
                    currency=snapshot.quote,
                ),
            ),
            PlanLeg(
                id="future-leg",
                instrument_id=snapshot.future_instrument_id,
                side="sell",
                target_notional=Money(
                    amount=hedge_notional,
                    currency=snapshot.quote,
                ),
            ),
        ),
        max_delta_pct=max_delta_pct,
        max_leverage=max_leverage,
        execution_mode="paper",
        capital_policy=CapitalPolicy(
            reserve_ratio=assumptions.reserve_ratio,
            futures_leverage=assumptions.futures_leverage,
        ),
        execution_cost_policy=ExecutionCostPolicy(
            spot_entry_fee_bps=assumptions.spot_entry_fee_bps,
            derivative_entry_fee_bps=assumptions.futures_entry_fee_bps,
            spot_exit_fee_bps=assumptions.spot_exit_fee_bps,
            derivative_exit_fee_bps=assumptions.futures_settlement_fee_bps,
            exit_buffer_bps=assumptions.exit_buffer_bps,
        ),
        deployment=deployment,
        expected_economics=expected_economics,
    )
