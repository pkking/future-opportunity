from __future__ import annotations

from datetime import date, timedelta
from typing import Any


QUARTERS = {
    "2025-Q3": {
        "start": "2025-07-01",
        "end": "2025-09-25",
        "future_id": "BTC-USDT-250926",
        "exit_market_date": "2025-09-25",
    },
    "2025-Q4": {
        "start": "2025-09-27",
        "end": "2025-12-25",
        "future_id": "BTC-USDT-251226",
        "exit_market_date": "2025-12-25",
    },
}
ENTRY_PROBE_DATES = (
    "2025-09-12", "2025-09-19",
    "2025-12-12", "2025-12-19",
)
SPOT_CATALOG_DATES = tuple(sorted(set(
    ENTRY_PROBE_DATES
    + ("2025-09-25", "2025-12-25")
)))


def quarter_capacity_report(
    candidate_counts: dict[str, int | None],
) -> dict[str, object]:
    if not isinstance(candidate_counts, dict):
        raise ValueError("capacity candidate counts must be a date map")
    result: dict[str, object] = {}
    for quarter, spec in QUARTERS.items():
        start = date.fromisoformat(spec["start"])
        end = date.fromisoformat(spec["end"])
        days = [
            (start + timedelta(days=i)).isoformat()
            for i in range((end - start).days + 1)
        ]
        absent = [day for day in days if day not in candidate_counts]
        if absent:
            raise ValueError("capacity source did not scan every quarter day")
        ready = [day for day in days if candidate_counts[day] == 1]
        missing = [day for day in days if candidate_counts[day] == 0]
        ambiguous = [
            day for day in days
            if isinstance(candidate_counts[day], int)
            and candidate_counts[day] > 1
        ]
        error = [day for day in days if candidate_counts[day] is None]
        invalid = [
            day for day in days
            if type(candidate_counts[day]) not in (int, type(None))
            or (
                type(candidate_counts[day]) is int
                and candidate_counts[day] < 0
            )
        ]
        if invalid:
            raise ValueError("invalid daily source capacity count")
        result[quarter] = {
            "expected_future_id": spec["future_id"],
            "expiry_exit_market_date": spec["exit_market_date"],
            "scanned_date_count": len(days),
            "unique_archive_day_count": len(ready),
            "missing_days": missing,
            "ambiguous_days": ambiguous,
            "query_error_days": error,
            "candidate_dates_with_unique_catalog_archive": ready,
            "source_calendar_complete": len(ready) == len(days),
            "exact_future_identity_for_each_day_verified": False,
        }
    return result


def paired_source_readiness(
    candidate_counts: dict[str, int | None],
    *,
    spot_catalog: dict[str, dict[str, Any]],
    futures_exit: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if set(spot_catalog) != set(SPOT_CATALOG_DATES):
        raise ValueError("SPOT source statuses must include all six fixed dates")
    exits = {spec["exit_market_date"] for spec in QUARTERS.values()}
    if set(futures_exit) != exits:
        raise ValueError("future exit statuses must include both fixed dates")

    quarter_counts = quarter_capacity_report(candidate_counts)
    spot_ready = all(
        item.get("status") == "unique_catalog_source"
        and isinstance(item.get("filename"), str)
        and bool(item["filename"])
        for item in spot_catalog.values()
    )
    exits_ready = all(
        item.get("status") == "identity_verified"
        and isinstance(item.get("raw_sha256"), str)
        and len(item["raw_sha256"]) == 64
        and all(char in "0123456789abcdefABCDEF" for char in item["raw_sha256"])
        for item in futures_exit.values()
    )
    return {
        "schema_version": 1,
        "evidence_type": "cash_2025_q3q4_entry_exit_source_readiness",
        "quarters": quarter_counts,
        "spot_catalog": spot_catalog,
        "futures_exit_archive_members": futures_exit,
        "spot_fixed_dates_catalog_ready": spot_ready,
        "future_exit_archive_identity_ready": exits_ready,
        "acquisition_ready": False,
        "entry_exit_orderbook_snapshots_verified": False,
        "no_economics_inspected": True,
        "note": (
            "FUTURES daily chain catalog coverage, SPOT daily catalog "
            "identity and FUTURES exit member identity do not prove paired "
            "00:15 snapshots, liquidity, or pre-expiry return completeness. "
            "No historical sample or promotion is created here."
        ),
    }
