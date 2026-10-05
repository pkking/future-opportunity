from __future__ import annotations

from decimal import Decimal

from future_opportunity.backtest.model import (
    HistoricalFundingCashFlowBound,
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
)


def bound_short_funding_cash_flow(
    funding: HistoricalFundingObservation,
    mark_candle: HistoricalMarkPriceCandle,
    *,
    base_quantity: Decimal,
) -> HistoricalFundingCashFlowBound:
    """Bound a linear short-perpetual funding cash flow using the settlement minute.

    The exact millisecond mark is intentionally not reconstructed. The official
    one-minute mark candle bounds the mark price during the settlement minute.
    """
    if base_quantity <= 0:
        raise ValueError("base_quantity must be positive")
    if funding.instrument_id != mark_candle.instrument_id:
        raise ValueError("funding and mark-price instruments must match")
    if not mark_candle.confirmed:
        raise ValueError("funding bound requires a confirmed mark-price candle")

    funding_minute = funding.funding_time.replace(second=0, microsecond=0)
    if mark_candle.started_at != funding_minute:
        raise ValueError(
            "mark-price candle must start at the funding settlement minute"
        )

    at_low = base_quantity * mark_candle.low_price * funding.funding_rate
    at_high = base_quantity * mark_candle.high_price * funding.funding_rate
    lower = min(at_low, at_high)
    upper = max(at_low, at_high)

    return HistoricalFundingCashFlowBound(
        funding_time=funding.funding_time,
        funding_rate=funding.funding_rate,
        mark_price_low=mark_candle.low_price,
        mark_price_high=mark_candle.high_price,
        cash_flow_lower=lower,
        cash_flow_upper=upper,
        evidence_complete=False,
        evidence_note=(
            "bounded by confirmed 1m mark-price candle; exact millisecond "
            "settlement mark is not available in the public funding archive"
        ),
    )


def sum_funding_cash_flow_bounds(
    bounds: tuple[HistoricalFundingCashFlowBound, ...],
) -> tuple[Decimal, Decimal]:
    return (
        sum((item.cash_flow_lower for item in bounds), Decimal(0)),
        sum((item.cash_flow_upper for item in bounds), Decimal(0)),
    )
