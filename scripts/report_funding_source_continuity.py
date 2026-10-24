"""Bounded multi-day immutable GitHub Funding ORIGINAL source continuity research.

Checks 2..90 completed UTC dates, all adjacent pairs including explicit gaps.
Requires the existing per-day GitHub independent-release-audit custody ledger
before loading SHA256-matched originals. Compares no OKX data from the network.
Stable overlap is NOT signed exchange publication, nor acquisition approval.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import httpx

from audit_funding_source_revision import (
    compare_overlapping_sources,
    fetch_original_capture,
)
from check_funding_release_watch import VALID_STATUS
from report_funding_prospective_custody_ledger import (
    build_report,
    eligible_days,
)

MAX_CONTINUITY_DAYS = 90
PAIRED_STATUS = "OVERLAP_VALUES_CONSISTENT_ONLY"
REVISION_STATUS = "SOURCE_REVISION_DETECTED"


def audit_continuity(
    start_date: str, end_date: str, *, now: Callable[[], datetime],
    client: httpx.Client, token: str,
    verify: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Classify every chronological edge without retaining all raw snapshots."""
    at = now()
    days = eligible_days(start_date, end_date, at)
    if not 2 <= len(days) <= MAX_CONTINUITY_DAYS:
        raise ValueError("continuity needs 2..90 completed UTC source dates")

    kwargs = {"verify": verify} if verify is not None else {}
    custody = build_report(
        start_date, end_date, now=lambda: at,
        client=client, token=token, **kwargs,
    )
    records = custody.get("days")
    if not isinstance(records, list) or len(records) != len(days):
        raise ValueError("custody ledger omitted required UTC dates")
    if any(
        not isinstance(record, dict)
        or record.get("entry_market_date") != day.isoformat()
        for day, record in zip(days, records, strict=True)
    ):
        raise ValueError("custody ledger day order/identity invalid")

    source_days: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    previous_day: str | None = None
    previous_digest: str | None = None

    for record in records:
        day = record["entry_market_date"]
        digest = record.get("archive_sha256")
        source_verified = (
            record.get("status") == VALID_STATUS
            and record.get("github_hosted_preentry_source_verified") is True
            and record.get("github_release_attestation_verified") is True
        )
        current: dict[str, Any] | None = None
        load_status = "UNASSESSED"
        reason: str | None = None
        if source_verified:
            try:
                current = fetch_original_capture(day, digest, client=client)
                load_status = "AUDITED_GITHUB_CUSTODY_ONLY"
            except (ValueError, KeyError, TypeError, httpx.HTTPError) as exc:
                # Preserve the audited status and original hash, but a
                # changed, missing or unreadable ZIP is NOT usable.
                reason = f"original ZIP source unavailable: {type(exc).__name__}"
        else:
            reason = "missing matching successful independent original-source audit"
        source_days.append({
            "date": day,
            "custody_status": record.get("status"),
            "original_archive_sha256": digest,
            "source_status": load_status,
            "reason": reason,
        })

        if previous_day is not None:
            pair: dict[str, Any] = {
                "earlier_day": previous_day,
                "later_day": day,
                "earlier_original_archive_sha256": previous_digest,
                "later_original_archive_sha256": digest,
                "status": "UNASSESSED",
                "comparison": None,
            }
            if previous is not None and current is not None:
                try:
                    comparison = compare_overlapping_sources(previous, current)
                    pair["comparison"] = comparison
                    pair["status"] = comparison["status"]
                except (KeyError, TypeError, ValueError) as exc:
                    pair["reason"] = (
                        f"comparison of authenticated originals failed: {type(exc).__name__}"
                    )
            else:
                pair["reason"] = "one or both exact adjacent source days unassessed"
            pairs.append(pair)

        # Rolling cache: only previous and current raw payload are ever live.
        previous = current
        previous_day = day
        previous_digest = digest

    revision_pairs = sum(p["status"] == REVISION_STATUS for p in pairs)
    consistent_pairs = sum(p["status"] == PAIRED_STATUS for p in pairs)
    unassessed_pairs = len(pairs) - consistent_pairs - revision_pairs
    assert len(pairs) == len(days) - 1
    status = (
        REVISION_STATUS if revision_pairs
        else ("UNASSESSED" if unassessed_pairs else PAIRED_STATUS)
    )
    return {
        "status": status,
        "scope": "adjacent_complete_utc_prospective_original_source_days_only",
        "start_date": start_date,
        "end_date": end_date,
        "checked_at": at.astimezone(UTC).isoformat(),
        "checked_day_count": len(days),
        "expected_pair_count": len(days) - 1,
        "consistent_pair_count": consistent_pairs,
        "revision_pair_count": revision_pairs,
        "unassessed_pair_count": unassessed_pairs,
        "every_adjacent_pair_assessed": unassessed_pairs == 0,
        "source_custody_ledger_status": custody.get("status"),
        "source_regime_coverage": custody.get("regime_coverage"),
        "source_days": source_days,
        "pairs": pairs,
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
        parser.error("a read-only GitHub Actions:read GH_TOKEN is required")
    try:
        with httpx.Client(timeout=httpx.Timeout(12.0), follow_redirects=False) as client:
            report = audit_continuity(
                args.start_date, args.end_date,
                now=lambda: datetime.now(UTC),
                client=client, token=token,
            )
    except ValueError as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, sort_keys=True, indent=2))
    if report["status"] != PAIRED_STATUS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
