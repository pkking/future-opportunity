from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.application.backtest.cash_and_carry import (
    HistoricalCashAndCarryCase,
    run_cash_and_carry_backtest,
)
from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    DeliverySettlement,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
)


BASE = datetime(2026, 1, 1, tzinfo=UTC)


def book(bid: str, ask: str, observed_at: datetime) -> OrderBook:
    return OrderBook(
        bids=(
            OrderBookLevel(
                price=Decimal(bid),
                quantity=Decimal(100),
            ),
        ),
        asks=(
            OrderBookLevel(
                price=Decimal(ask),
                quantity=Decimal(100),
            ),
        ),
        observed_at=observed_at,
    )


def case(
    case_id: str,
    *,
    future_bid: str,
    settlement_price: str,
    spot_close_bid: str,
    day_offset: int,
) -> HistoricalCashAndCarryCase:
    observed_at = BASE + timedelta(days=day_offset)
    expiry = observed_at + timedelta(days=90)
    return HistoricalCashAndCarryCase(
        case_id=case_id,
        entry=CashAndCarryMarketSnapshot(
            venue="fixture",
            base="BTC",
            quote="USDT",
            spot_instrument_id="fixture:spot",
            future_instrument_id=f"fixture:future:{case_id}",
            spot_book=book("99", "100", observed_at),
            future_book=book(
                future_bid,
                str(Decimal(future_bid) + Decimal(1)),
                observed_at,
            ),
            expiry=expiry,
            observed_at=observed_at,
        ),
        settlement=DeliverySettlement(
            venue="fixture",
            future_instrument_id=f"fixture:future:{case_id}",
            settlement_price=Decimal(settlement_price),
            settled_at=expiry,
        ),
        spot_close_instrument_id="fixture:spot",
        spot_close_book=book(
            spot_close_bid,
            str(Decimal(spot_close_bid) + Decimal("0.5")),
            expiry + timedelta(seconds=1),
        ),
        evidence_ids=(f"fixture:{case_id}",),
    )


@pytest.mark.asyncio
async def test_cash_backtest_aggregates_qualified_and_realized_cases() -> None:
    assumptions = CashAndCarryAssumptions(
        spot_entry_fee_bps=Decimal(0),
        futures_entry_fee_bps=Decimal(0),
        spot_exit_fee_bps=Decimal(0),
        futures_settlement_fee_bps=Decimal(0),
        exit_buffer_bps=Decimal(0),
    )
    report = await run_cash_and_carry_backtest(
        (
            case(
                "positive-a",
                future_bid="104",
                settlement_price="102",
                spot_close_bid="102",
                day_offset=0,
            ),
            case(
                "backwardation",
                future_bid="98",
                settlement_price="101",
                spot_close_bid="101",
                day_offset=1,
            ),
            case(
                "positive-b",
                future_bid="106",
                settlement_price="103",
                spot_close_bid="103",
                day_offset=2,
            ),
        ),
        capital=Decimal(10_000),
        assumptions=assumptions,
    )

    assert report.sample_count == 3
    assert report.qualified_count == 2
    assert report.qualification_rate == Decimal(2) / Decimal(3)
    assert report.closed_count == 2
    assert report.complete_return_count == 2
    assert report.minimum_realized_net_return is not None
    assert report.maximum_realized_net_return is not None
    assert report.maximum_realized_net_return > report.minimum_realized_net_return

    rejected = next(item for item in report.cases if not item.qualified)
    assert "future_not_in_contango" in rejected.qualification_reasons
    assert rejected.realized_net_return is None

    for accepted in (item for item in report.cases if item.qualified):
        assert accepted.return_complete is True
        assert accepted.initial_delta_pct == Decimal(0)
        assert accepted.realized_net_return is not None
        assert accepted.evidence_ids
