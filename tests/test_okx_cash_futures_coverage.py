from __future__ import annotations

import pytest

from future_opportunity.backtest.cash_source_coverage import (
    CASH_COVERAGE_MODULES,
    CASH_POSITIVE_CONTROL_DATES,
    CASH_WAVE_002_DATES,
    CASH_WAVE_003_DATES,
    cash_coverage_status,
    cash_futures_coverage_dates,
    summarize_cash_futures_coverage,
)


def _observation(
    module: str,
    market_date: str,
    candidate_count: int,
) -> dict[str, object]:
    return {
        "module": module,
        "market_date": market_date,
        "candidate_count": candidate_count,
    }


def test_cash_futures_coverage_dates_are_locked_and_unique() -> None:
    dates = cash_futures_coverage_dates()

    assert dates == (
        CASH_POSITIVE_CONTROL_DATES
        + CASH_WAVE_002_DATES
        + CASH_WAVE_003_DATES
    )
    assert len(dates) == 33
    assert len(set(dates)) == 33
    assert len(CASH_POSITIVE_CONTROL_DATES) == 5
    assert len(CASH_WAVE_002_DATES) == 14
    assert len(CASH_WAVE_003_DATES) == 14


@pytest.mark.parametrize(
    ("candidate_count", "expected"),
    [
        (0, "no_candidate"),
        (1, "unique_candidate"),
        (2, "ambiguous_candidates"),
        (9, "ambiguous_candidates"),
    ],
)
def test_cash_coverage_status(
    candidate_count: int,
    expected: str,
) -> None:
    assert cash_coverage_status(candidate_count) == expected


def test_cash_coverage_status_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        cash_coverage_status(-1)


def test_summarize_cash_futures_coverage_separates_cohorts() -> None:
    observations: list[dict[str, object]] = []
    dates = cash_futures_coverage_dates()

    for module in CASH_COVERAGE_MODULES:
        for market_date in dates:
            if market_date in CASH_POSITIVE_CONTROL_DATES:
                count = 1
            elif module == "4":
                count = 0
            else:
                count = 2
            observations.append(_observation(module, market_date, count))

    summary = summarize_cash_futures_coverage(observations)

    assert summary["date_count"] == 33
    assert summary["observation_count"] == 66
    assert summary["modules"]["4"] == {
        "total_dates": 33,
        "no_candidate": 28,
        "unique_candidate": 5,
        "ambiguous_candidates": 0,
        "positive_controls": {
            "total": 5,
            "unique_candidate": 5,
        },
        "wave_dates": {
            "total": 28,
            "unique_candidate": 0,
        },
    }
    assert summary["modules"]["6"] == {
        "total_dates": 33,
        "no_candidate": 0,
        "unique_candidate": 5,
        "ambiguous_candidates": 28,
        "positive_controls": {
            "total": 5,
            "unique_candidate": 5,
        },
        "wave_dates": {
            "total": 28,
            "unique_candidate": 0,
        },
    }


def test_summarize_cash_futures_coverage_requires_complete_matrix() -> None:
    observations = [
        _observation("4", market_date, 0)
        for market_date in cash_futures_coverage_dates()
    ]

    with pytest.raises(ValueError, match="missing coverage observations"):
        summarize_cash_futures_coverage(observations)
