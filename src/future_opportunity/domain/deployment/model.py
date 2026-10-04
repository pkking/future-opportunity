from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from future_opportunity.domain.capital.model import allocate_isolated_hedge


class LiquidityPolicy(StrEnum):
    STRICT = "strict"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class DeploymentAssessment:
    policy: LiquidityPolicy
    max_impact_bps: Decimal
    requested_capital: Decimal
    reserve_amount: Decimal
    requested_spot_notional: Decimal
    capacity_spot_notional: Decimal
    actual_spot_notional: Decimal
    actual_hedge_notional: Decimal
    futures_margin: Decimal
    unused_capital: Decimal
    partial_deployment: bool
    capacity_sufficient: bool

    @property
    def executable(self) -> bool:
        if self.actual_spot_notional <= 0:
            return False
        return (
            self.capacity_sufficient
            if self.policy is LiquidityPolicy.STRICT
            else True
        )


def assess_liquidity_bounded_deployment(
    *,
    capital: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
    hedge_notional_ratio: Decimal,
    capacity_spot_notional: Decimal,
    policy: LiquidityPolicy = LiquidityPolicy.STRICT,
    max_impact_bps: Decimal = Decimal(10),
) -> DeploymentAssessment:
    if capacity_spot_notional < 0:
        raise ValueError("capacity_spot_notional must be non-negative")
    if max_impact_bps < 0:
        raise ValueError("max_impact_bps must be non-negative")

    requested = allocate_isolated_hedge(
        capital,
        reserve_ratio,
        futures_leverage,
        hedge_notional_ratio=hedge_notional_ratio,
    )
    capacity_sufficient = capacity_spot_notional >= requested.spot_notional

    if capacity_sufficient:
        actual_spot_notional = requested.spot_notional
    elif policy is LiquidityPolicy.PARTIAL:
        actual_spot_notional = capacity_spot_notional
    else:
        actual_spot_notional = Decimal(0)

    actual_hedge_notional = actual_spot_notional * hedge_notional_ratio
    futures_margin = actual_hedge_notional / futures_leverage
    unused_capital = (
        capital
        - requested.reserve_amount
        - actual_spot_notional
        - futures_margin
    )

    return DeploymentAssessment(
        policy=policy,
        max_impact_bps=max_impact_bps,
        requested_capital=capital,
        reserve_amount=requested.reserve_amount,
        requested_spot_notional=requested.spot_notional,
        capacity_spot_notional=capacity_spot_notional,
        actual_spot_notional=actual_spot_notional,
        actual_hedge_notional=actual_hedge_notional,
        futures_margin=futures_margin,
        unused_capital=unused_capital,
        partial_deployment=(
            actual_spot_notional > 0
            and actual_spot_notional < requested.spot_notional
        ),
        capacity_sufficient=capacity_sufficient,
    )
