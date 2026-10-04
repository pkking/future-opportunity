from decimal import Decimal

from future_opportunity.domain.deployment.model import (
    LiquidityPolicy,
    assess_liquidity_bounded_deployment,
)


def test_strict_policy_rejects_when_capacity_is_below_requested_notional() -> None:
    assessment = assess_liquidity_bounded_deployment(
        capital=Decimal(10_000),
        reserve_ratio=Decimal("0.10"),
        futures_leverage=Decimal(1),
        hedge_notional_ratio=Decimal(1),
        capacity_spot_notional=Decimal(3_000),
    )

    assert assessment.policy is LiquidityPolicy.STRICT
    assert assessment.requested_spot_notional == Decimal(4_500)
    assert assessment.actual_spot_notional == Decimal(0)
    assert assessment.capacity_sufficient is False
    assert assessment.executable is False
    assert assessment.partial_deployment is False
    assert assessment.unused_capital == Decimal(9_000)


def test_partial_policy_explicitly_caps_deployment_and_keeps_idle_capital_visible() -> None:
    assessment = assess_liquidity_bounded_deployment(
        capital=Decimal(10_000),
        reserve_ratio=Decimal("0.10"),
        futures_leverage=Decimal(1),
        hedge_notional_ratio=Decimal(1),
        capacity_spot_notional=Decimal(3_000),
        policy=LiquidityPolicy.PARTIAL,
    )

    assert assessment.requested_spot_notional == Decimal(4_500)
    assert assessment.actual_spot_notional == Decimal(3_000)
    assert assessment.actual_hedge_notional == Decimal(3_000)
    assert assessment.futures_margin == Decimal(3_000)
    assert assessment.reserve_amount == Decimal(1_000)
    assert assessment.unused_capital == Decimal(3_000)
    assert assessment.partial_deployment is True
    assert assessment.executable is True


def test_partial_policy_uses_full_target_when_capacity_is_sufficient() -> None:
    assessment = assess_liquidity_bounded_deployment(
        capital=Decimal(10_000),
        reserve_ratio=Decimal("0.10"),
        futures_leverage=Decimal(1),
        hedge_notional_ratio=Decimal("1.02"),
        capacity_spot_notional=Decimal(10_000),
        policy=LiquidityPolicy.PARTIAL,
        max_impact_bps=Decimal(5),
    )

    expected = Decimal(9_000) / Decimal("2.02")
    assert assessment.max_impact_bps == Decimal(5)
    assert assessment.actual_spot_notional == expected
    assert assessment.actual_hedge_notional == expected * Decimal("1.02")
    assert assessment.partial_deployment is False
    assert assessment.capacity_sufficient is True
    assert abs(assessment.unused_capital) < Decimal("1e-20")
