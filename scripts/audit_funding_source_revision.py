"""Compare revisable OKX values in TWO GitHub-held Funding source originals.

Research-only diagnostic: stable overlap does not prove independent OKX
publication time, signed exchange provenance, acquisition eligibility or PnL.
No exchange API access. No writes to GitHub or original immutable Releases.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import zipfile
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

import httpx

from audit_vps_funding_capture import (
    MAX_ORIGINAL_ZIP_BYTES,
    SOURCE_MEMBERS,
    _json_object,
)
from future_opportunity.backtest.funding_raw_feature_lineage import (
    _finite,
    _funding_index,
    _spot_index,
)
from publish_vps_funding_github_release import REPO
from report_funding_prospective_custody_ledger import build_report, eligible_days

RAW_CAPTURE_MAX_BYTES = 2_000_000


def pair_days(earlier: str, later: str, now: datetime) -> tuple[str, str]:
    days = eligible_days(earlier, later, now)
    if len(days) != 2 or days[1] - days[0] != timedelta(days=1):
        raise ValueError("source revision requires two consecutive complete UTC days")
    return days[0].isoformat(), days[1].isoformat()


def fetch_original_capture(
    day: str, expected_archive_sha256: str, *, client: httpx.Client,
) -> dict[str, Any]:
    """Retrieve only GitHub's already independently audited immutable ZIP.

    The SHA is obtained from a separate full signed-audit-checked ledger,
    rather than self-computed from the downloaded ZIP.
    """
    if (
        not isinstance(expected_archive_sha256, str)
        or len(expected_archive_sha256) != 64
        or any(c not in "0123456789abcdef" for c in expected_archive_sha256)
    ):
        raise ValueError("independently reviewed original ZIP digest required")
    url = f"https://github.com/{REPO}/releases/download/funding-vps-{day}/original-source.zip"
    response = client.get(url, follow_redirects=True)
    response.raise_for_status()
    original = response.content
    if not 0 < len(original) <= MAX_ORIGINAL_ZIP_BYTES:
        raise ValueError("GitHub original source ZIP is missing or oversized")
    if hashlib.sha256(original).hexdigest() != expected_archive_sha256:
        raise ValueError("GitHub original source ZIP differs from independently reviewed digest")
    try:
        with zipfile.ZipFile(io.BytesIO(original)) as archive:
            members = archive.infolist()
            if len(members) != len(SOURCE_MEMBERS) or {
                item.filename for item in members
            } != set(SOURCE_MEMBERS):
                raise ValueError("original source ZIP has duplicate, missing or extra files")
            for item in members:
                if item.is_dir() or item.flag_bits & 1 or not 0 < item.file_size <= (
                    RAW_CAPTURE_MAX_BYTES
                ):
                    raise ValueError("original source ZIP includes unsafe member")
            raw = archive.read("raw-api-capture.json")
            if len(raw) > RAW_CAPTURE_MAX_BYTES:
                raise ValueError("original raw JSON exceeds bounded archive limit")
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise ValueError("original source ZIP cannot be read safely") from exc

    parsed = _json_object(raw, "original raw-api-capture")
    if parsed.get("start_date") != day or parsed.get("end_date") != day:
        raise ValueError("original capture day identity does not match audited Release")
    # Reuse exact source-shape, instrument, numeric and duplicate-key validators.
    _funding_index(parsed.get("funding_response"))
    _spot_index(parsed.get("spot_response"))
    return parsed


def compare_overlapping_sources(
    earlier_capture: dict[str, Any],
    later_capture: dict[str, Any],
) -> dict[str, Any]:
    """Report semantic revisions only where the *same* source keys overlap."""
    old_funding = _funding_index(earlier_capture["funding_response"])
    new_funding = _funding_index(later_capture["funding_response"])
    old_spot = _spot_index(earlier_capture["spot_response"])
    new_spot = _spot_index(later_capture["spot_response"])

    f_common = sorted(old_funding.keys() & new_funding.keys())
    funding_changes: list[dict[str, str]] = []
    for moment in f_common:
        old_rate = _finite(old_funding[moment]["realizedRate"], "old realizedRate")
        new_rate = _finite(new_funding[moment]["realizedRate"], "new realizedRate")
        if old_rate != new_rate:
            funding_changes.append({
                "funding_time": moment.isoformat(),
                "earlier_realized_rate": str(old_rate),
                "later_realized_rate": str(new_rate),
            })

    s_common = sorted(old_spot.keys() & new_spot.keys())
    candle_changes: list[dict[str, str]] = []
    confirmation_conflicts: list[str] = []
    confirmed_overlap_count = 0
    for moment in s_common:
        prev, next_ = old_spot[moment], new_spot[moment]
        if prev[8] != next_[8]:
            confirmation_conflicts.append(moment.isoformat())
        if prev[8] == next_[8] == "1":
            confirmed_overlap_count += 1
            old_close = _finite(prev[4], "old confirmed close", positive=True)
            new_close = _finite(next_[4], "new confirmed close", positive=True)
            if old_close != new_close:
                candle_changes.append({
                    "candle_open_at": moment.isoformat(),
                    "earlier_confirmed_close": str(old_close),
                    "later_confirmed_close": str(new_close),
                })
    if funding_changes or candle_changes or confirmation_conflicts:
        status = "SOURCE_REVISION_DETECTED"
    elif f_common and confirmed_overlap_count:
        status = "OVERLAP_VALUES_CONSISTENT_ONLY"
    else:
        status = "UNASSESSED_INSUFFICIENT_OVERLAP"

    return {
        "status": status,
        "funding": {
            "overlap_count": len(f_common),
            "only_in_earlier_count": len(old_funding.keys() - new_funding.keys()),
            "only_in_later_count": len(new_funding.keys() - old_funding.keys()),
            "realized_rate_revisions": funding_changes,
        },
        "spot": {
            "confirmed_close_overlap_count": confirmed_overlap_count,
            "only_in_earlier_count": len(old_spot.keys() - new_spot.keys()),
            "only_in_later_count": len(new_spot.keys() - old_spot.keys()),
            "confirmation_state_conflicts": confirmation_conflicts,
            "confirmed_close_revisions": candle_changes,
        },
    }


def audit_pair(
    earlier: str, later: str, *, now: Callable[[], datetime],
    client: httpx.Client, token: str,
    verify: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Reuse ledger signed-audit preconditions before comparing original bytes."""
    checked_at = now()
    d1, d2 = pair_days(earlier, later, checked_at)
    ledger = build_report(
        d1, d2, now=lambda: checked_at, client=client, token=token,
        verify=verify,
    )
    summary: dict[str, Any] = {
        "status": "UNASSESSED",
        "scope": "two_consecutive_prospective_UTC_source_days",
        "earlier_day": d1,
        "later_day": d2,
        "source_custody_ledger_status": ledger["status"],
        "original_archive_sha256": {
            row["entry_market_date"]: row.get("archive_sha256")
            for row in ledger["days"]
        },
        "comparison": None,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "market_wide_opportunity_arrival_rate": None,
    }
    if ledger["status"] != "AUDITED_GITHUB_CUSTODY_ONLY":
        summary["reason"] = "one or more immutable GitHub source/audit checks incomplete"
        return summary
    try:
        originals = [
            fetch_original_capture(
                day, summary["original_archive_sha256"][day], client=client
            )
            for day in (d1, d2)
        ]
        comparison = compare_overlapping_sources(*originals)
    except (ValueError, KeyError, TypeError, httpx.HTTPError) as exc:
        summary["reason"] = f"original source revision review failed: {type(exc).__name__}"
        return summary
    summary["comparison"] = comparison
    summary["status"] = comparison["status"]
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--earlier-day", required=True)
    parser.add_argument("--later-day", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        parser.error("a read-only GH_TOKEN (Actions:read) is required")
    try:
        with httpx.Client(timeout=httpx.Timeout(12.0), follow_redirects=False) as client:
            report = audit_pair(
                args.earlier_day, args.later_day, now=lambda: datetime.now(UTC),
                client=client, token=token,
            )
    except ValueError as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps(report, sort_keys=True, indent=2))
    if report["status"] != "OVERLAP_VALUES_CONSISTENT_ONLY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
