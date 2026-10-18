"""Bounded UTC-midnight gate for a best-effort scheduled *read-only* source capture.

GitHub cron is not a clock: it can start late or drop the job entirely.
The original capture script must independently enforce the 00:00..00:15
HTTP transaction deadline even after this preparatory gate succeeds.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime, time as clock_time, timedelta
from pathlib import Path
from typing import Callable

SCHEDULE_UTC = clock_time(hour=23, minute=37)
CUTOFF = timedelta(minutes=15)
POLL_SECONDS = 10.0
MAX_POLLS = 180  # strict finite wait even if the runner UTC clock freezes


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("scheduled source gate requires an aware UTC clock")
    return value.astimezone(UTC)


def target_midnight(started: datetime) -> datetime:
    """Only warm-up evening or actual 00:00..00:15 may enter the source gate.

    Late cron delivery must never cause a wait until *another* midnight.
    The target is always derived from actual UTC; no calendar backdating.
    """
    started = _utc(started)
    midnight = datetime.combine(started.date(), clock_time.min, tzinfo=UTC)
    if started.time() >= SCHEDULE_UTC:
        return midnight + timedelta(days=1)
    if started < midnight + CUTOFF:
        return midnight
    raise ValueError("scheduled preentry runner missed current UTC window")


def wait_for_preentry_window(
    now: Callable[[], datetime] | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> dict[str, str | bool]:
    """Wait for real UTC midnight, with bounded polling and fail-closed expiry."""
    now = now or (lambda: datetime.now(UTC))
    sleeper = sleeper or time.sleep
    started = _utc(now())
    midnight = target_midnight(started)
    cutoff = midnight + CUTOFF
    previous = started
    for _ in range(MAX_POLLS):
        observed = _utc(now())
        if observed < previous:
            raise ValueError("scheduled preentry UTC clock moved backwards")
        previous = observed
        if observed >= cutoff:
            raise ValueError("scheduled preentry UTC 00:15 deadline missed")
        if observed >= midnight:
            return {
                "status": "utc_window_open_for_attempt_only",
                "runner_observed_at": observed.isoformat(),
                "target_entry_date": midnight.date().isoformat(),
                "entry_at": cutoff.isoformat(),
                "point_in_time_publication_verified": False,
            }
        remaining = (midnight - observed).total_seconds()
        sleeper(min(POLL_SECONDS, remaining))
    raise ValueError("scheduled preentry maximum wait budget exhausted")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = wait_for_preentry_window()
        print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    except Exception as exc:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "error.json").write_text(json.dumps({
            "status": "UNASSESSED",
            "phase": "scheduled_preentry_wait",
            "error_type": type(exc).__name__,
            "reason": str(exc),
            "point_in_time_publication_verified": False,
            "acquisition_approved": False,
            "promotion_approved": False,
        }, sort_keys=True, indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()
