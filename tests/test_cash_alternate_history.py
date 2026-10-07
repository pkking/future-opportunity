from __future__ import annotations

from datetime import date

import pytest

from future_opportunity.backtest.cash_alternate_history import (
    CASH_ALTERNATE_HISTORY_DATES,
    CASH_APPROVED_FUTURE_ID,
    CASH_ENTRY_TIME_UTC,
    classify_alternate_observation,
    subtract_calendar_months,
    summarize_alternate_history_coverage,
    trade_retention_eligible,
)


def _observation(
    source: str,
    role: str,
    market_date: str,
    *,
    code: str = "0",
    returned: int = 1,
    target: int = 1,
    retention_eligible: bool = True,
) -> dict[str, object]:
    return {
        "source": source,
        "instrument_role": role,
        "market_date": market_date,
        "okx_code": code,
        "returned_count": returned,
        "target_window_count": target,
        "retention_eligible": retention_eligible,
    }


def test_alternate_history_inputs_are_locked() -> None:
    assert len(CASH_ALTERNATE_HISTORY_DATES) == 28
    assert len(set(CASH_ALTERNATE_HISTORY_DATES)) == 28
    assert CASH_ALTERNATE_HISTORY_DATES[0] == "2026-07-02"
    assert CASH_ALTERNATE_HISTORY_DATES[-1] == "2026-09-20"
    assert CASH_APPROVED_FUTURE_ID == "BTC-USDT-260925"
    assert CASH_ENTRY_TIME_UTC == "00:15:00"


@pytest.mark.parametrize(
    ("value", "months", "expected"),
    [
        (date(2026, 10, 7), 3, date(2026, 7, 7)),
        (date(2024, 5, 31), 3, date(2024, 2, 29)),
        (date(2026, 1, 31), 1, date(2025, 12, 31)),
    ],
)
def test_subtract_calendar_months(
    value: date,
    months: int,
    expected: date,
) -> None:
    assert subtract_calendar_months(value, months) == expected


def test_trade_retention_uses_calendar_month_boundary() -> None:
    probe_date = date(2026, 10, 7)
    assert not trade_retention_eligible(
        "2026-07-05",
        probe_date=probe_date,
    )
    assert trade_retention_eligible(
        "2026-07-07",
        probe_date=probe_date,
    )


@pytest.mark.parametrize(
    ("observation", "expected"),
    [
        (_observation("candles", "future", "2026-07-02"), "target_covered"),
        (
            _observation(
                "trades",
                "future",
                "2026-07-02",
                retention_eligible=False,
                returned=0,
                target=0,
            ),
            "retention_excluded",
        ),
        (
            _observation(
                "candles",
                "future",
                "2026-07-02",
                code="51001",
                returned=0,
                target=0,
            ),
            "api_error",
        ),
        (
            _observation(
                "candles",
                "future",
                "2026-07-02",
                returned=2,
                target=0,
            ),
            "returned_outside_target",
        ),
        (
            _observation(
                "candles",
                "future",
                "2026-07-02",
                returned=0,
                target=0,
            ),
            "no_data",
        ),
    ],
)
def test_classify_alternate_observation(
    observation: dict[str, object],
    expected: str,
) -> None:
    assert classify_alternate_observation(observation) == expected


def test_summary_requires_all_candle_dates_and_separates_sources() -> None:
    observations: list[dict[str, object]] = []
    for market_date in CASH_ALTERNATE_HISTORY_DATES:
        observations.append(
            _observation("candles", "future", market_date)
        )
        observations.append(
            _observation("candles", "spot", market_date)
        )
        observations.append(
            _observation(
                "trades",
                "future",
                market_date,
                retention_eligible=False,
                returned=0,
                target=0,
            )
        )

    summary = summarize_alternate_history_coverage(observations)

    assert summary["date_count"] == 28
    assert summary["coverage"]["candles:future"]["target_covered"] == 28
    assert summary["coverage"]["candles:spot"]["target_covered"] == 28
    assert summary["coverage"]["trades:future"]["retention_excluded"] == 28


def test_summary_rejects_missing_candle_observation() -> None:
    observations = [
        _observation("candles", "future", market_date)
        for market_date in CASH_ALTERNATE_HISTORY_DATES
    ]
    with pytest.raises(ValueError, match="missing required candlestick"):
        summarize_alternate_history_coverage(observations)
