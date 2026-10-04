from datetime import UTC, datetime
from decimal import Decimal

from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel
from future_opportunity.domain.position.model import LegPosition, Position, PositionState
from future_opportunity.domain.risk.invariants import (
    evaluate_carry_positive,
    evaluate_exit_liquidity,
    evaluate_leg_integrity,
    margin_safety_unassessed,
    venue_exposure_unassessed,
)
from future_opportunity.domain.risk.model import InvariantState


def position() -> Position:
    return Position(
        id="pos",
        strategy_plan_id="plan",
        state=PositionState.HEDGED,
        legs=(
            LegPosition("spot", Decimal(1), Decimal(100)),
            LegPosition("hedge", Decimal(-1), Decimal(-101)),
        ),
        delta_notional=Decimal(0),
        delta_pct=Decimal(0),
    )


def test_risk_invariants_distinguish_assessed_from_unassessed() -> None:
    pos = position()
    leg = evaluate_leg_integrity(pos, ("spot", "hedge"))
    carry = evaluate_carry_positive(Decimal("0.01"))

    now = datetime.now(UTC)
    books = {
        "spot": OrderBook(
            bids=(OrderBookLevel(Decimal(100), Decimal(10)),),
            asks=(OrderBookLevel(Decimal(101), Decimal(10)),),
            observed_at=now,
        ),
        "hedge": OrderBook(
            bids=(OrderBookLevel(Decimal(100), Decimal(10)),),
            asks=(OrderBookLevel(Decimal(101), Decimal(10)),),
            observed_at=now,
        ),
    }
    exit_liquidity = evaluate_exit_liquidity(
        pos,
        books,
        max_impact_bps=Decimal(10),
    )

    assert leg.state is InvariantState.SATISFIED
    assert carry.state is InvariantState.SATISFIED
    assert exit_liquidity.state is InvariantState.SATISFIED
    assert margin_safety_unassessed().state is InvariantState.UNASSESSED
    assert venue_exposure_unassessed().state is InvariantState.UNASSESSED
