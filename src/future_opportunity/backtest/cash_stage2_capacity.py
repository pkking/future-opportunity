from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date


CASH_STAGE2_TARGET_DAYS = 30
CASH_STAGE2_CAPACITY_MODULE = "4"
CASH_STAGE2_CAPACITY_FAMILY = "BTC-USDT"
CASH_STAGE2_CAPACITY_SCAN_START = date(2026, 1, 1)
CASH_STAGE2_CAPACITY_SCAN_END = date(2026, 6, 26)


def evenly_spaced_dates(
    dates: Sequence[str],
    count: int,
) -> tuple[str, ...]:
    ordered = tuple(sorted(set(dates)))
    if count < 0:
        raise ValueError("count must be non-negative")
    if count > len(ordered):
        raise ValueError("count exceeds available dates")
    if count == 0:
        return ()
    if count == len(ordered):
        return ordered

    # Pick the center of count equal-size rank buckets. Selection depends only
    # on source availability, never on economics observed on a selected day.
    indices = tuple(
        ((2 * index + 1) * len(ordered)) // (2 * count)
        for index in range(count)
    )
    selected = tuple(ordered[index] for index in indices)
    if len(set(selected)) != count:
        raise AssertionError("evenly spaced selection produced duplicate dates")
    return selected


def plan_cash_stage2_capacity(
    candidate_counts: Mapping[str, int | None],
    *,
    pinned_dates: Sequence[str],
    target_days: int = CASH_STAGE2_TARGET_DAYS,
) -> dict[str, object]:
    if target_days <= 0:
        raise ValueError("target_days must be positive")

    ordered_dates = tuple(sorted(candidate_counts))
    if not ordered_dates:
        raise ValueError("capacity planner requires observed dates")

    pinned = tuple(sorted(set(pinned_dates)))
    remaining = max(target_days - len(pinned), 0)

    ready: list[str] = []
    missing: list[str] = []
    ambiguous: list[str] = []
    query_error: list[str] = []

    for market_date in ordered_dates:
        try:
            date.fromisoformat(market_date)
        except ValueError as error:
            raise ValueError(f"invalid observed market date: {market_date}") from error
        count = candidate_counts[market_date]
        if count is None:
            query_error.append(market_date)
        elif count < 0:
            raise ValueError("candidate count must be non-negative")
        elif count == 0:
            missing.append(market_date)
        elif count == 1:
            ready.append(market_date)
        else:
            ambiguous.append(market_date)

    pinned_set = set(pinned)
    usable = tuple(item for item in ready if item not in pinned_set)
    capacity_sufficient = len(usable) >= remaining
    selected_count = min(remaining, len(usable))
    selected = evenly_spaced_dates(usable, selected_count)

    return {
        "target_pinned_day_count": target_days,
        "current_pinned_day_count": len(pinned),
        "remaining_day_count": remaining,
        "scan_date_count": len(ordered_dates),
        "unique_ready_count": len(ready),
        "unique_ready_unpinned_count": len(usable),
        "missing_count": len(missing),
        "ambiguous_count": len(ambiguous),
        "query_error_count": len(query_error),
        "capacity_sufficient": capacity_sufficient,
        "selected_candidate_count": len(selected),
        "selected_candidate_dates": list(selected),
        "ready_unpinned_dates": list(usable),
        "missing_dates": missing,
        "ambiguous_dates": ambiguous,
        "query_error_dates": query_error,
        "selection_semantics": (
            "deterministic_even_rank_buckets_over_unique_ready_unpinned_dates;"
            " availability_only_no_economics"
        ),
    }
