from __future__ import annotations

from collections.abc import Mapping

from future_opportunity.backtest.cash_source_coverage import (
    CASH_WAVE_002_DATES,
    CASH_WAVE_003_DATES,
)


CASH_SOURCE_READINESS_DATES = CASH_WAVE_002_DATES + CASH_WAVE_003_DATES
CASH_SOURCE_READINESS_MODULE = "4"
CASH_SOURCE_READINESS_FAMILY = "BTC-USDT"


def summarize_cash_source_readiness(
    candidate_counts: Mapping[str, int | None],
) -> dict[str, object]:
    required = tuple(CASH_SOURCE_READINESS_DATES)
    if set(candidate_counts) != set(required):
        missing_keys = sorted(set(required) - set(candidate_counts))
        unexpected_keys = sorted(set(candidate_counts) - set(required))
        raise ValueError(
            "readiness observations must exactly match canonical dates; "
            f"missing={missing_keys}, unexpected={unexpected_keys}"
        )

    ready_dates: list[str] = []
    missing_dates: list[str] = []
    ambiguous_dates: list[str] = []
    query_error_dates: list[str] = []

    for market_date in required:
        count = candidate_counts[market_date]
        if count is None:
            query_error_dates.append(market_date)
        elif count < 0:
            raise ValueError("candidate count must be non-negative")
        elif count == 0:
            missing_dates.append(market_date)
        elif count == 1:
            ready_dates.append(market_date)
        else:
            ambiguous_dates.append(market_date)

    return {
        "required_count": len(required),
        "ready_count": len(ready_dates),
        "missing_count": len(missing_dates),
        "ambiguous_count": len(ambiguous_dates),
        "query_error_count": len(query_error_dates),
        "all_ready": len(ready_dates) == len(required),
        "ready_dates": ready_dates,
        "missing_dates": missing_dates,
        "ambiguous_dates": ambiguous_dates,
        "query_error_dates": query_error_dates,
    }
