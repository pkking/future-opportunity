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
        asks=(OrderBookLevel(price=Decimal(100), quantity=Decimal(100)),),
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


def test_evaluation_accounts_for_deployed_capital_and_costs() -> None:
    result = evaluate_funding_carry(
        make_snapshot(),
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    assert result.expected_funding_rate_per_period == Decimal("0.00010")
    assert result.funding_periods_per_day == Decimal(3)
    assert result.positive_funding_ratio_7d == Decimal(1)
    assert result.deployed_notional == Decimal(4_500)
    assert result.futures_margin == Decimal(4_500)
    assert result.reserve_amount == Decimal(1_000)
    assert result.gross_return_horizon == Decimal("0.0040500")
    assert result.assumed_round_trip_fee_return == Decimal("0.00135")
    assert result.estimated_round_trip_slippage_return == Decimal(0)
    assert result.expected_net_return_horizon == Decimal("0.0027000")
    assert result.annualized_equivalent == Decimal("0.0328500")


def test_funding_interval_is_derived_from_history() -> None:
    snapshot = make_snapshot()
    now = snapshot.observed_at
    four_hour_history = tuple(
        FundingObservation(
            rate=Decimal("0.0001"),
            funding_time=now - timedelta(hours=4 * index),
        )
        for index in range(120)
    )
    result = evaluate_funding_carry(
        FundingCarryMarketSnapshot(
            venue=snapshot.venue,
            base=snapshot.base,
            quote=snapshot.quote,
            spot_instrument_id=snapshot.spot_instrument_id,
            perpetual_instrument_id=snapshot.perpetual_instrument_id,
            spot_book=snapshot.spot_book,
            perpetual_book=snapshot.perpetual_book,
            mark_price=snapshot.mark_price,
            last_funding_rate=snapshot.last_funding_rate,
            next_funding_time=snapshot.next_funding_time,
            funding_history=four_hour_history,
            observed_at=now,
        ),
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(),
    )

    assert result.funding_periods_per_day == Decimal(6)
