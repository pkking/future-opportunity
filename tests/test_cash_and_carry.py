from datetime import UTC, datetime, timedelta
from decimal import Decimal

from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
    evaluate_cash_and_carry,
)


def test_cash_and_carry_reports_convergent_return_to_expiry() -> None:
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

    result = evaluate_cash_and_carry(
        snapshot,
        capital=Decimal(10_000),
        assumptions=CashAndCarryAssumptions(
            spot_entry_fee_bps=Decimal(0),
            futures_entry_fee_bps=Decimal(0),
            spot_exit_fee_bps=Decimal(0),
            futures_settlement_fee_bps=Decimal(0),
            exit_buffer_bps=Decimal(0),
        ),
    )

    assert result.return_character == "convergent"
    assert result.gross_basis_return_on_notional == Decimal("0.02")
    assert result.expected_net_return_to_expiry > Decimal(0)
    assert result.annualized_equivalent > result.expected_net_return_to_expiry
    assert (
        result.reserve_amount + result.spot_notional + result.futures_margin
        == Decimal(10_000)
    )
