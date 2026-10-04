from __future__ import annotations

from decimal import Decimal

from future_opportunity.domain.market.snapshot import OrderBook
from future_opportunity.domain.position.model import Position
from future_opportunity.domain.risk.invariants import (
    evaluate_carry_positive,
    evaluate_delta_neutrality,
    evaluate_exit_liquidity,
    evaluate_leg_integrity,
    margin_safety_unassessed,
    venue_exposure_unassessed,
)
from future_opportunity.domain.risk.model import RiskReport
from future_opportunity.domain.strategy.model import StrategyPlan


def build_paper_risk_report(
    position: Position,
    plan: StrategyPlan,
    expected_net_return: Decimal,
    books: dict[str, OrderBook],
    max_exit_impact_bps: Decimal = Decimal(10),
) -> RiskReport:
    expected_instruments = tuple(leg.instrument_id for leg in plan.legs)

    return RiskReport(
        invariants=(
            evaluate_delta_neutrality(position, plan.max_delta_pct),
            evaluate_leg_integrity(position, expected_instruments),
            evaluate_carry_positive(expected_net_return),
            evaluate_exit_liquidity(
                position,
                books,
                max_impact_bps=max_exit_impact_bps,
            ),
            margin_safety_unassessed(),
            venue_exposure_unassessed(),
        )
    )
