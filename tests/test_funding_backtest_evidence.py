from datetime import UTC, datetime
from decimal import Decimal

import pytest

from future_opportunity.backtest.funding_evidence import (
    bound_short_funding_cash_flow,
    sum_funding_cash_flow_bounds,
)
from future_opportunity.backtest.model import (
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
)


TIME = datetime(2026, 9, 1, 8, tzinfo=UTC)


def funding(rate: str) -> HistoricalFundingObservation:
    return HistoricalFundingObservation(
        instrument_id="BTC-USDT-SWAP",
        source_line=2,
        funding_time=TIME,
        funding_rate=Decimal(rate),
    )


def candle() -> HistoricalMarkPriceCandle:
    return HistoricalMarkPriceCandle(
        instrument_id="BTC-USDT-SWAP",
        started_at=TIME,
        open_price=Decimal(100_000),
        high_price=Decimal(101_000),
        low_price=Decimal(99_000),
        close_price=Decimal(100_500),
        confirmed=True,
    )


def test_positive_funding_short_receipt_is_bounded_by_mark_low_high() -> None:
    result = bound_short_funding_cash_flow(
        funding("0.001"),
        candle(),
        base_quantity=Decimal("0.1"),
    )

    assert result.cash_flow_lower == Decimal("9.9")
    assert result.cash_flow_upper == Decimal("10.1")
    assert result.evidence_complete is False


def test_negative_funding_short_payment_keeps_lower_upper_ordered() -> None:
    result = bound_short_funding_cash_flow(
        funding("-0.001"),
        candle(),
        base_quantity=Decimal("0.1"),
    )

    assert result.cash_flow_lower == Decimal("-10.1")
    assert result.cash_flow_upper == Decimal("-9.9")


def test_funding_bounds_require_same_confirmed_settlement_minute() -> None:
    wrong_time = HistoricalMarkPriceCandle(
        instrument_id="BTC-USDT-SWAP",
        started_at=datetime(2026, 9, 1, 8, 1, tzinfo=UTC),
        open_price=Decimal(100),
        high_price=Decimal(101),
        low_price=Decimal(99),
        close_price=Decimal(100),
        confirmed=True,
    )
    with pytest.raises(ValueError, match="settlement minute"):
        bound_short_funding_cash_flow(
            funding("0.001"),
            wrong_time,
            base_quantity=Decimal(1),
        )


def test_funding_bounds_sum_as_intervals() -> None:
    positive = bound_short_funding_cash_flow(
        funding("0.001"),
        candle(),
        base_quantity=Decimal("0.1"),
    )
    negative = bound_short_funding_cash_flow(
        funding("-0.001"),
        candle(),
        base_quantity=Decimal("0.1"),
    )

    assert sum_funding_cash_flow_bounds((positive, negative)) == (
        Decimal("-0.2"),
        Decimal("0.2"),
    )
