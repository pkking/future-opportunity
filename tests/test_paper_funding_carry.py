from datetime import UTC, datetime, timedelta
from decimal import Decimal

from future_opportunity.application.execute.paper_funding_carry import (
    execute_paper_funding_carry,
)
from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.risk.model import InvariantState
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


def test_paper_execution_builds_delta_neutral_combination() -> None:
    now = datetime.now(UTC)
    spot = OrderBook(
        bids=(OrderBookLevel(price=Decimal(99), quantity=Decimal(20)),),
        asks=(OrderBookLevel(price=Decimal(100), quantity=Decimal(20)),),
        observed_at=now,
    )
    perpetual = OrderBook(
        bids=(OrderBookLevel(price=Decimal(101), quantity=Decimal(20)),),
        asks=(OrderBookLevel(price=Decimal(102), quantity=Decimal(20)),),
        observed_at=now,
    )
    snapshot = FundingCarryMarketSnapshot(
        venue="binance",
        base="BTC",
        quote="USDT",
        spot_instrument_id="binance:BTCUSDT:spot",
        perpetual_instrument_id="binance:BTCUSDT:perpetual",
        spot_book=spot,
        perpetual_book=perpetual,
        mark_price=Decimal(101),
        last_funding_rate=Decimal("0.0001"),
        next_funding_time=now + timedelta(hours=8),
        funding_history=(),
        observed_at=now,
    )

    result = execute_paper_funding_carry(
        position_id="pos-1",
        strategy_plan_id="plan-1",
        snapshot=snapshot,
        capital=Decimal(1_000),
        assumptions=FundingCarryAssumptions(),
    )

    assert result.position.delta_pct == Decimal(0)
    assert result.position.legs[0].quantity == -result.position.legs[1].quantity

    invariant = evaluate_delta_neutrality(
        result.position,
        max_delta_pct=Decimal("0.005"),
    )
    assert invariant.state is InvariantState.SATISFIED
