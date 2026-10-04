from datetime import UTC, datetime, timedelta
from decimal import Decimal

from future_opportunity.application.execute.paper_cash_and_carry import (
    execute_paper_cash_and_carry,
)
from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.risk.model import InvariantState
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions


def test_paper_cash_and_carry_is_base_delta_neutral() -> None:
    now = datetime.now(UTC)
    spot = OrderBook(
        bids=(OrderBookLevel(price=Decimal(99), quantity=Decimal(100)),),
        asks=(OrderBookLevel(price=Decimal(100), quantity=Decimal(100)),),
        observed_at=now,
    )
    future = OrderBook(
        bids=(OrderBookLevel(price=Decimal(102), quantity=Decimal(100)),),
        asks=(OrderBookLevel(price=Decimal(103), quantity=Decimal(100)),),
        observed_at=now,
    )
    snapshot = CashAndCarryMarketSnapshot(
        venue="okx",
        base="BTC",
        quote="USDT",
        spot_instrument_id="okx:BTC-USDT:spot",
        future_instrument_id="okx:BTC-USDT-261225:future",
        spot_book=spot,
        future_book=future,
        expiry=now + timedelta(days=90),
        observed_at=now,
    )

    result = execute_paper_cash_and_carry(
        position_id="pos-carry",
        strategy_plan_id="plan-carry",
        snapshot=snapshot,
        capital=Decimal(10_000),
        assumptions=CashAndCarryAssumptions(),
    )

    assert result.position.delta_pct == Decimal(0)
    invariant = evaluate_delta_neutrality(
        result.position,
        max_delta_pct=Decimal("0.005"),
    )
    assert invariant.state is InvariantState.SATISFIED
