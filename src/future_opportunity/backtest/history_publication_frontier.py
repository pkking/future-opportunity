from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable


HISTORY_FRONTIER_MODULES = ("1", "2", "4", "5", "6")
HISTORY_FRONTIER_START = date(2026, 6, 1)
HISTORY_FRONTIER_END = date(2026, 10, 6)
HISTORY_FRONTIER_PROBE_DATE = date(2026, 10, 7)
MAX_DAILY_QUERY_DAYS = 10


def inclusive_date_chunks(
    start: date,
    end: date,
    *,
    max_days: int = MAX_DAILY_QUERY_DAYS,
) -> tuple[tuple[date, date], ...]:
    if max_days <= 0:
        raise ValueError("max_days must be positive")
    if end < start:
        raise ValueError("end must not precede start")

    chunks: list[tuple[date, date]] = []
    cursor = start
    width = timedelta(days=max_days - 1)
    while cursor <= end:
        chunk_end = min(cursor + width, end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return tuple(chunks)


def summarize_module_frontier(
    *,
    module: str,
    available_dates: Iterable[date],
    scan_start: date = HISTORY_FRONTIER_START,
    scan_end: date = HISTORY_FRONTIER_END,
    probe_date: date = HISTORY_FRONTIER_PROBE_DATE,
) -> dict[str, object]:
    if module not in HISTORY_FRONTIER_MODULES:
        raise ValueError(f"unsupported frontier module: {module}")
    if scan_end < scan_start:
        raise ValueError("scan_end must not precede scan_start")

    dates = tuple(sorted(set(available_dates)))
    for item in dates:
        if item < scan_start or item > scan_end:
            raise ValueError(
                f"available date {item.isoformat()} outside scan interval"
            )

    if not dates:
        return {
            "module": module,
            "available_count": 0,
            "first_available_date": None,
            "latest_available_date": None,
            "latest_age_days": None,
            "internal_gap_count": 0,
            "internal_gaps": [],
            "frontier_contiguous": False,
        }

    first = dates[0]
    latest = dates[-1]
    available = set(dates)
    internal_gaps: list[str] = []
    cursor = first
    while cursor <= latest:
        if cursor not in available:
            internal_gaps.append(cursor.isoformat())
        cursor += timedelta(days=1)

    return {
        "module": module,
        "available_count": len(dates),
        "first_available_date": first.isoformat(),
        "latest_available_date": latest.isoformat(),
        "latest_age_days": (probe_date - latest).days,
        "internal_gap_count": len(internal_gaps),
        "internal_gaps": internal_gaps,
        "frontier_contiguous": len(internal_gaps) == 0,
    }


def summarize_cross_module_frontier(
    module_summaries: Iterable[dict[str, object]],
) -> dict[str, object]:
    summaries = tuple(module_summaries)
    modules = [str(item["module"]) for item in summaries]
    if sorted(modules) != sorted(HISTORY_FRONTIER_MODULES):
        raise ValueError(
            "cross-module summary requires exactly modules 1/2/4/5/6"
        )

    latest = {
        str(item["module"]): item.get("latest_available_date")
        for item in summaries
    }
    non_null = {value for value in latest.values() if value is not None}
    return {
        "latest_available_by_module": latest,
        "frontier_agreement": len(non_null) == 1 and len(non_null) > 0,
        "all_modules_contiguous": all(
            bool(item.get("frontier_contiguous")) for item in summaries
        ),
    }
