from datetime import UTC, datetime, timedelta
from decimal import Decimal

from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    evaluate_funding_carry,
)


def make_snapshot() -> FundingCarryMarketSnapshot:
    now = datetime.now(UTC)
    history = tuple(
        FundingObservation(
            rate=Decimal("0.0001"),
            funding_time=now - timedelta(hours=8 * index),
        )
        for index in range(90)
    )
    book = OrderBook(
        bids=(OrderBookLevel(price=Decimal(100), quantity=Decimal(100)),),
        asks=(OrderBookLevel(price=Decimal(101), quantity=Decimal(100)),),
        observed_at=now,
    )
    return FundingCarryMarketSnapshot(
        venue="binance",
        base="BTC",
        quote="USDT",
        spot_instrument_id="binance:BTCUSDT:spot",
        perpetual_instrument_id="binance:BTCUSDT:perpetual",
        spot_book=book,
        perpetual_book=book,
        mark_price=Decimal("100.5"),
        last_funding_rate=Decimal("0.0001"),
        next_funding_time=now + timedelta(hours=8),
        funding_history=history,
        observed_at=now,
    )


def test_evaluation_separates_carry_from_fee_assumptions() -> None:
    result = evaluate_funding_carry(
        make_snapshot(),
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    assert result.expected_funding_rate_per_period == Decimal("0.00010")
    assert result.positive_funding_ratio_7d == Decimal(1)
    assert result.gross_return_horizon == Decimal("0.00900")
    assert result.assumed_round_trip_fee_return == Decimal("0.003")
    assert result.expected_net_return_horizon == Decimal("0.00600")
    assert result.annualized_equivalent == Decimal("0.07300")
