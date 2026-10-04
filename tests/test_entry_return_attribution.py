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
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


def test_entry_costs_are_attributed_from_fill_facts() -> None:
    now = datetime.now(UTC)
    spot = OrderBook(
        bids=(OrderBookLevel(Decimal(99), Decimal(100)),),
        asks=(
            OrderBookLevel(Decimal(100), Decimal(1)),
            OrderBookLevel(Decimal(101), Decimal(100)),
        ),
        observed_at=now,
    )
    perpetual = OrderBook(
        bids=(
            OrderBookLevel(Decimal(102), Decimal(1)),
            OrderBookLevel(Decimal(101), Decimal(100)),
        ),
        asks=(OrderBookLevel(Decimal(103), Decimal(100)),),
        observed_at=now,
    )
    snapshot = FundingCarryMarketSnapshot(
        venue="fake",
        base="BTC",
        quote="USDT",
        spot_instrument_id="spot",
        perpetual_instrument_id="perp",
        spot_book=spot,
        perpetual_book=perpetual,
        mark_price=Decimal("102.5"),
        last_funding_rate=Decimal("0.0001"),
        next_funding_time=now + timedelta(hours=8),
        funding_history=(),
        observed_at=now,
    )

    result = execute_paper_funding_carry(
        position_id="position",
        strategy_plan_id="plan",
        snapshot=snapshot,
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(
            spot_taker_fee_bps=Decimal(10),
            perpetual_taker_fee_bps=Decimal(5),
        ),
    )

    assert result.entry_return.trading_fees == sum(
        (fill.fee for fill in result.fills),
        Decimal(0),
    )
    assert result.entry_return.slippage == sum(
        (fill.slippage_quote for fill in result.fills),
        Decimal(0),
    )
    assert result.position.realized_pnl == result.entry_return.net_pnl
    assert result.position.opened_at is not None
