from __future__ import annotations

from typing import Any


CASH_COVERAGE_MODULES = ("4", "6")
CASH_POSITIVE_CONTROL_DATES = (
    "2026-06-01",
    "2026-06-02",
    "2026-06-03",
    "2026-06-04",
    "2026-06-08",
)
CASH_WAVE_002_DATES = (
    "2026-07-02",
    "2026-07-03",
    "2026-07-05",
    "2026-07-07",
    "2026-07-10",
    "2026-07-12",
    "2026-07-15",
    "2026-07-17",
    "2026-07-18",
    "2026-07-21",
    "2026-07-23",
    "2026-07-25",
    "2026-07-27",
    "2026-07-31",
)
CASH_WAVE_003_DATES = (
    "2026-08-02",
    "2026-08-04",
    "2026-08-10",
    "2026-08-12",
    "2026-08-16",
    "2026-08-21",
    "2026-08-26",
    "2026-08-28",
    "2026-08-31",
    "2026-09-06",
    "2026-09-09",
    "2026-09-14",
    "2026-09-18",
    "2026-09-20",
)


def cash_futures_coverage_dates() -> tuple[str, ...]:
    return (
        CASH_POSITIVE_CONTROL_DATES
        + CASH_WAVE_002_DATES
        + CASH_WAVE_003_DATES
    )


def cash_coverage_status(candidate_count: int) -> str:
    if candidate_count < 0:
        raise ValueError("candidate_count must be non-negative")
    if candidate_count == 0:
        return "no_candidate"
    if candidate_count == 1:
        return "unique_candidate"
    return "ambiguous_candidates"


def summarize_cash_futures_coverage(
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_dates = set(cash_futures_coverage_dates())
    expected_modules = set(CASH_COVERAGE_MODULES)
    seen: set[tuple[str, str]] = set()
    by_module: dict[str, dict[str, Any]] = {}

    for observation in observations:
        module = str(observation["module"])
        market_date = str(observation["market_date"])
        candidate_count = int(observation["candidate_count"])
        if module not in expected_modules:
            raise ValueError(f"unexpected coverage module: {module}")
        if market_date not in expected_dates:
            raise ValueError(f"unexpected coverage date: {market_date}")
        key = (module, market_date)
        if key in seen:
            raise ValueError(f"duplicate coverage observation: {key}")
        seen.add(key)

        status = cash_coverage_status(candidate_count)
        module_summary = by_module.setdefault(
            module,
            {
                "total_dates": 0,
                "no_candidate": 0,
                "unique_candidate": 0,
                "ambiguous_candidates": 0,
                "positive_controls": {
                    "total": len(CASH_POSITIVE_CONTROL_DATES),
                    "unique_candidate": 0,
                },
                "wave_dates": {
                    "total": (
                        len(CASH_WAVE_002_DATES)
                        + len(CASH_WAVE_003_DATES)
                    ),
                    "unique_candidate": 0,
                },
            },
        )
        module_summary["total_dates"] += 1
        module_summary[status] += 1
        if market_date in CASH_POSITIVE_CONTROL_DATES:
            if status == "unique_candidate":
                module_summary["positive_controls"]["unique_candidate"] += 1
        elif status == "unique_candidate":
            module_summary["wave_dates"]["unique_candidate"] += 1

    expected_keys = {
        (module, market_date)
        for module in CASH_COVERAGE_MODULES
        for market_date in cash_futures_coverage_dates()
    }
    missing = sorted(expected_keys - seen)
    if missing:
        raise ValueError(f"missing coverage observations: {missing}")

    return {
        "date_count": len(expected_dates),
        "observation_count": len(observations),
        "modules": by_module,
    }
