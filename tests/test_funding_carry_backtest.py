from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.application.backtest.funding_carry import (
    HistoricalFundingCarryCase,
    run_funding_carry_backtest,
)
from future_opportunity.backtest.model import (
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
)
from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
)


BASE = datetime(2026, 9, 1, tzinfo=UTC)


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


def snapshot(
    observed_at: datetime,
    *,
    rate: str = "0.001",
    spot_bid: str = "99.9",
    spot_ask: str = "100",
    perp_bid: str = "100.1",
    perp_ask: str = "100.2",
) -> FundingCarryMarketSnapshot:
    history = tuple(
        FundingObservation(
            rate=Decimal(rate),
            funding_time=observed_at - timedelta(hours=8 * index),
        )
        for index in range(90)
    )
    return FundingCarryMarketSnapshot(
        venue="fixture",
        base="BTC",
        quote="USDT",
        spot_instrument_id="fixture:spot",
        perpetual_instrument_id="fixture:perp",
        spot_book=book(spot_bid, spot_ask, observed_at),
        perpetual_book=book(perp_bid, perp_ask, observed_at),
        mark_price=(Decimal(perp_bid) + Decimal(perp_ask)) / Decimal(2),
        last_funding_rate=Decimal(rate),
        next_funding_time=observed_at + timedelta(hours=8),
        funding_history=history,
        observed_at=observed_at,
    )


def historical_funding(
    hour: int,
    *,
    rate: str = "0.001",
) -> HistoricalFundingObservation:
    return HistoricalFundingObservation(
        instrument_id="fixture:perp",
        source_line=hour + 2,
        funding_time=BASE + timedelta(hours=hour),
        funding_rate=Decimal(rate),
    )


def mark(hour: int) -> HistoricalMarkPriceCandle:
    started_at = BASE + timedelta(hours=hour)
    return HistoricalMarkPriceCandle(
        instrument_id="fixture:perp",
        started_at=started_at,
        open_price=Decimal(100),
        high_price=Decimal(101),
        low_price=Decimal(99),
        close_price=Decimal("100.5"),
        confirmed=True,
    )


@pytest.mark.asyncio
async def test_funding_backtest_reports_conservative_realized_interval() -> None:
    case = HistoricalFundingCarryCase(
        case_id="one-day",
        entry=snapshot(BASE),
        exit=snapshot(
            BASE + timedelta(days=1),
            spot_bid="100",
            spot_ask="100.1",
            perp_bid="100",
            perp_ask="100.1",
        ),
        funding=(
            historical_funding(8),
            historical_funding(16),
            historical_funding(24),
        ),
        mark_prices=(mark(8), mark(16), mark(24)),
        evidence_ids=("fixture:l2", "fixture:funding", "fixture:mark"),
    )
    report = await run_funding_carry_backtest(
        (case,),
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(
            horizon_days=1,
            spot_taker_fee_bps=Decimal(0),
            perpetual_taker_fee_bps=Decimal(0),
        ),
    )

    assert report.sample_count == 1
    assert report.qualified_count == 1
    assert report.interval_evidence_complete_count == 1

    result = report.cases[0]
    assert result.funding_event_count == 3
    assert result.funding_interval_evidence_complete is True
    assert result.funding_cash_flow_lower is not None
    assert result.funding_cash_flow_upper is not None
    assert result.funding_cash_flow_lower < result.funding_cash_flow_upper
    assert result.realized_return_lower is not None
    assert result.realized_return_upper is not None
    assert result.realized_return_lower < result.realized_return_upper
    assert result.initial_delta_pct == Decimal(0)
    assert result.evidence_ids == (
        "fixture:l2",
        "fixture:funding",
        "fixture:mark",
    )


@pytest.mark.asyncio
async def test_funding_backtest_keeps_realized_interval_unassessed_when_mark_missing() -> None:
    case = HistoricalFundingCarryCase(
        case_id="missing-mark",
        entry=snapshot(BASE),
        exit=snapshot(BASE + timedelta(days=1)),
        funding=(
            historical_funding(8),
            historical_funding(16),
        ),
        mark_prices=(mark(8),),
    )
    report = await run_funding_carry_backtest(
        (case,),
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(
            horizon_days=1,
            spot_taker_fee_bps=Decimal(0),
            perpetual_taker_fee_bps=Decimal(0),
        ),
    )

    result = report.cases[0]
    assert result.qualified is True
    assert result.funding_interval_evidence_complete is False
    assert result.realized_return_lower is None
    assert result.realized_return_upper is None


@pytest.mark.asyncio
async def test_funding_backtest_preserves_unqualified_case_without_execution() -> None:
    case = HistoricalFundingCarryCase(
        case_id="negative-funding",
        entry=snapshot(BASE, rate="-0.001"),
        exit=snapshot(BASE + timedelta(days=1), rate="-0.001"),
        funding=(),
        mark_prices=(),
    )
    report = await run_funding_carry_backtest(
        (case,),
        capital=Decimal(10_000),
        assumptions=FundingCarryAssumptions(horizon_days=1),
    )

    result = report.cases[0]
    assert result.qualified is False
    assert "expected_funding_not_positive" in result.qualification_reasons
    assert result.realized_return_lower is None
    assert result.assessed_ex_funding_pnl is None
