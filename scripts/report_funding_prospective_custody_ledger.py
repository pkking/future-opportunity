"""Read-only longitudinal GitHub custody report for prospective Funding evidence.

This replays the *original* immutable Release ZIP per completed UTC day and
requires the matching successful independent release.published audit. A valid
GitHub source timestamp does NOT establish when OKX disseminated the values.
No exchange API, GitHub writes, historical corpus mutation or trading.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable

import httpx

from check_funding_release_watch import (
    AUDIT_WORKFLOW,
    FIRST_DAY,
    _api_failure,
    _day,
    _receipt,
    _utc_now,
    check_day,
    summarize_audited_regimes,
)
from publish_vps_funding_github_release import API, REPO

MAX_WINDOW_DAYS = 90
MAX_AUDIT_PAGES = 20
AUDIT_PAGE_SIZE = 100


def eligible_days(start_date: str, end_date: str, now: datetime) -> list[date]:
    """Canonical inclusive date range; strictly completed UTC source windows."""
    first, last = _day(start_date), _day(end_date)
    if first < FIRST_DAY or last < first:
        raise ValueError("ledger date range is outside prospective rollout")
    days = (last - first).days + 1
    if days > MAX_WINDOW_DAYS:
        raise ValueError("ledger range exceeds 90 complete UTC days")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("ledger needs a timezone-aware UTC clock")
    instant = now.astimezone(UTC)
    deadline = datetime.combine(last, time.min, tzinfo=UTC) + timedelta(minutes=15)
    if instant < deadline:
        raise ValueError("cannot audit a UTC source window before its deadline")
    return [first + timedelta(days=i) for i in range(days)]


def fetch_window_audits(
    client: httpx.Client, token: str, *, start_day: date,
) -> list[dict[str, Any]]:
    """Fetch enough newest-first release audit history to cover start_day.

    The separate GitHub release audit is the verification witness. Do not use
    only the last 100 runs for a 90-day cohort: older successful releases may
    otherwise be silently classified as having no independent auditor.
    """
    if not token:
        raise ValueError("read-only GitHub Actions token required")
    earliest = datetime.combine(start_day, time.min, tzinfo=UTC)
    runs: list[dict[str, Any]] = []
    last_created: datetime | None = None
    for page in range(1, MAX_AUDIT_PAGES + 1):
        response = client.get(
            f"{API}/actions/workflows/{AUDIT_WORKFLOW}/runs",
            params={"event": "release", "per_page": AUDIT_PAGE_SIZE, "page": page},
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        data = response.json()
        batch = data.get("workflow_runs") if isinstance(data, dict) else None
        if not isinstance(batch, list) or len(batch) > AUDIT_PAGE_SIZE:
            raise ValueError("invalid GitHub release-audit page")
        if not batch:
            return runs
        for item in batch:
            if not isinstance(item, dict):
                raise ValueError("invalid GitHub release-audit run")
            raw = item.get("created_at")
            if not isinstance(raw, str):
                raise ValueError("missing independent audit run creation time")
            try:
                created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("invalid independent audit run creation time") from exc
            if created.tzinfo is None:
                raise ValueError("independent audit creation time must be UTC-aware")
            created = created.astimezone(UTC)
            if last_created is not None and created > last_created:
                raise ValueError("GitHub audit history is not newest-first")
            last_created = created
            runs.append(item)
        # Once all later audits are encountered, older ones cannot apply to
        # the requested UTC source window. Don't infer missing on truncation.
        if last_created is not None and last_created < earliest:
            return runs
        if len(batch) < AUDIT_PAGE_SIZE:
            return runs
    raise ValueError("GitHub audit history pagination exceeded safe limit")


def build_report(
    start_date: str, end_date: str, *, now: Callable[[], datetime],
    client: httpx.Client, token: str,
    verify: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return auditable exact-day results; missing evidence remains UNASSESSED."""
    instant = _utc_now(now)
    days = eligible_days(start_date, end_date, instant)
    try:
        audits = fetch_window_audits(client, token, start_day=days[0])
    except (httpx.HTTPError, ValueError, TypeError, json.JSONDecodeError) as exc:
        reason = f"independent audit history unavailable: {_api_failure(exc)}"
        results = [_receipt(day, "UNASSESSED", reason) for day in days]
    else:
        results = []
        for day in days:
            try:
                options = {"verify": verify} if verify is not None else {}
                results.append(
                    check_day(day, now=instant, client=client, audits=audits, **options)
                )
            except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
                # Keep every requested date in the ledger, even when replay
                # unexpectedly fails or one source is unavailable.
                results.append(_receipt(day, "UNASSESSED", _api_failure(exc)))
    try:
        coverage = summarize_audited_regimes(results)
        healthy = coverage["github_audited_day_count"] == len(days)
    except (ValueError, TypeError) as exc:
        coverage = {
            "status": "UNASSESSED",
            "reason": str(exc)[:256],
            "point_in_time_publication_verified": False,
            "acquisition_approved": False,
            "promotion_approved": False,
        }
        healthy = False
    return {
        "status": "AUDITED_GITHUB_CUSTODY_ONLY" if healthy else "UNASSESSED",
        "repo": REPO,
        "checked_at": instant.isoformat(),
        "start_date": start_date,
        "end_date": end_date,
        "checked_day_count": len(days),
        "github_audited_day_count": coverage.get("github_audited_day_count", 0),
        "days": results,
        "regime_coverage": coverage,
        "github_only_read_only": True,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "market_wide_opportunity_arrival_rate": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        parser.error("a read-only GH_TOKEN (Actions:read) is required")
    try:
        with httpx.Client(timeout=httpx.Timeout(12.0), follow_redirects=False) as client:
            report = build_report(
                args.start_date, args.end_date, now=lambda: datetime.now(UTC),
                client=client, token=token,
            )
    except ValueError as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Do not overwrite existing evidence of a previous run.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "AUDITED_GITHUB_CUSTODY_ONLY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
