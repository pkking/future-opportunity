from __future__ import annotations

import json
from datetime import date, timedelta


def historical_date_range(
    start_date: str,
    end_date: str,
    *,
    max_days: int = 31,
) -> tuple[str, ...]:
    if max_days <= 0:
        raise ValueError("max_days must be positive")
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as error:
        raise ValueError("historical dates must use YYYY-MM-DD") from error
    if end < start:
        raise ValueError("end_date must not be before start_date")

    count = (end - start).days + 1
    if count > max_days:
        raise ValueError(
            f"historical date range contains {count} days; "
            f"maximum is {max_days}"
        )
    return tuple(
        (start + timedelta(days=offset)).isoformat()
        for offset in range(count)
    )


def historical_date_range_json(
    start_date: str,
    end_date: str,
    *,
    max_days: int = 31,
) -> str:
    return json.dumps(
        list(
            historical_date_range(
                start_date,
                end_date,
                max_days=max_days,
            )
        ),
        separators=(",", ":"),
    )
