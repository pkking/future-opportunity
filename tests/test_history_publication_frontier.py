from __future__ import annotations

from datetime import date

import pytest

from future_opportunity.backtest.history_publication_frontier import (
    HISTORY_FRONTIER_MODULES,
    inclusive_date_chunks,
    summarize_cross_module_frontier,
    summarize_module_frontier,
)


def test_inclusive_date_chunks_respect_ten_day_limit() -> None:
    chunks = inclusive_date_chunks(date(2026, 6, 1), date(2026, 10, 6))

    assert chunks[0] == (date(2026, 6, 1), date(2026, 6, 10))
    assert chunks[-1] == (date(2026, 9, 29), date(2026, 10, 6))
    assert all((end - start).days + 1 <= 10 for start, end in chunks)

    flattened = []
    for start, end in chunks:
        cursor = start
        while cursor <= end:
            flattened.append(cursor)
            cursor = cursor.fromordinal(cursor.toordinal() + 1)
    assert flattened == [
        date.fromordinal(value)
        for value in range(
            date(2026, 6, 1).toordinal(),
            date(2026, 10, 6).toordinal() + 1,
        )
    ]


def test_inclusive_date_chunks_reject_invalid_range() -> None:
    with pytest.raises(ValueError, match="end must not precede"):
        inclusive_date_chunks(date(2026, 6, 2), date(2026, 6, 1))


def test_module_frontier_reports_contiguous_cutoff() -> None:
    available = [
        date.fromordinal(value)
        for value in range(
            date(2026, 6, 1).toordinal(),
            date(2026, 6, 30).toordinal() + 1,
        )
    ]
    result = summarize_module_frontier(
        module="4",
        available_dates=available,
    )

    assert result["first_available_date"] == "2026-06-01"
    assert result["latest_available_date"] == "2026-06-30"
    assert result["latest_age_days"] == 99
    assert result["internal_gap_count"] == 0
    assert result["frontier_contiguous"] is True


def test_module_frontier_reports_internal_gap() -> None:
    result = summarize_module_frontier(
        module="5",
        available_dates=(
            date(2026, 6, 1),
            date(2026, 6, 2),
            date(2026, 6, 4),
        ),
    )

    assert result["latest_available_date"] == "2026-06-04"
    assert result["internal_gaps"] == ["2026-06-03"]
    assert result["frontier_contiguous"] is False


def test_cross_module_frontier_requires_all_modules() -> None:
    summaries = [
        summarize_module_frontier(
            module=module,
            available_dates=(date(2026, 6, 1),),
        )
        for module in HISTORY_FRONTIER_MODULES
    ]
    result = summarize_cross_module_frontier(summaries)

    assert result["frontier_agreement"] is True
    assert result["all_modules_contiguous"] is True
    assert set(result["latest_available_by_module"]) == set(
        HISTORY_FRONTIER_MODULES
    )


def test_cross_module_frontier_detects_disagreement() -> None:
    summaries = [
        summarize_module_frontier(
            module=module,
            available_dates=(
                date(2026, 6, 1),
                date(2026, 6, 2)
                if module == "1"
                else date(2026, 6, 1),
            ),
        )
        for module in HISTORY_FRONTIER_MODULES
    ]
    result = summarize_cross_module_frontier(summaries)

    assert result["frontier_agreement"] is False
