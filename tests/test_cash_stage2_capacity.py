from __future__ import annotations

import pytest

from future_opportunity.backtest.cash_stage2_capacity import (
    evenly_spaced_dates,
    plan_cash_stage2_capacity,
)


def test_evenly_spaced_selection_is_deterministic_and_unique() -> None:
    dates = tuple(f"2026-06-{day:02d}" for day in range(1, 11))

    selected = evenly_spaced_dates(dates, 4)

    assert selected == (
        "2026-06-02",
        "2026-06-04",
        "2026-06-07",
        "2026-06-09",
    )
    assert len(set(selected)) == 4


def test_capacity_plan_reaches_target_from_unique_unpinned_dates() -> None:
    counts = {
        f"2026-05-{day:02d}": 1
        for day in range(1, 32)
    }
    pinned = (
        "2026-05-01",
        "2026-05-02",
        "2026-05-03",
        "2026-05-04",
        "2026-05-05",
    )

    result = plan_cash_stage2_capacity(
        counts,
        pinned_dates=pinned,
        target_days=30,
    )

    assert result["current_pinned_day_count"] == 5
    assert result["remaining_day_count"] == 25
    assert result["unique_ready_unpinned_count"] == 26
    assert result["capacity_sufficient"] is True
    assert result["selected_candidate_count"] == 25
    assert len(set(result["selected_candidate_dates"])) == 25
    assert not set(result["selected_candidate_dates"]) & set(pinned)


def test_capacity_plan_reports_shortfall_without_lowering_target() -> None:
    counts = {
        f"2026-06-{day:02d}": 1
        for day in range(1, 21)
    }

    result = plan_cash_stage2_capacity(
        counts,
        pinned_dates=("2026-06-01",) * 5,
        target_days=30,
    )

    # Duplicate pinned inputs describe one distinct pinned date.
    assert result["current_pinned_day_count"] == 1
    assert result["remaining_day_count"] == 29
    assert result["unique_ready_unpinned_count"] == 19
    assert result["capacity_sufficient"] is False
    assert result["selected_candidate_count"] == 19


def test_capacity_plan_separates_missing_ambiguous_and_query_errors() -> None:
    counts = {
        "2026-06-01": 1,
        "2026-06-02": 0,
        "2026-06-03": 2,
        "2026-06-04": None,
    }

    result = plan_cash_stage2_capacity(
        counts,
        pinned_dates=(),
        target_days=3,
    )

    assert result["unique_ready_count"] == 1
    assert result["missing_count"] == 1
    assert result["ambiguous_count"] == 1
    assert result["query_error_count"] == 1
    assert result["capacity_sufficient"] is False


def test_evenly_spaced_selection_rejects_over_request() -> None:
    with pytest.raises(ValueError, match="exceeds available"):
        evenly_spaced_dates(("2026-06-01",), 2)
