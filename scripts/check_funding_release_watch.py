"""Read-only daily GitHub prospective Funding Release health and gap watcher.

This checks *absence* of already expected GitHub Release evidence, unlike the
release.published verifier which cannot run if there was no release event.
Only GitHub HTTPS GETs; no market API, archive mutations, or promotion.

GitHub Actions schedule is best-effort. A rolling-day lookback catches many
delayed/dropped watcher runs, but cannot promise a run if GitHub cron is lost.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable

import httpx

from audit_github_vps_release import verify_release
from publish_vps_funding_github_release import API, REPO

FIRST_DAY = date(2026, 10, 23)
ENTRY_MINUTE = 15
AUDIT_WORKFLOW = "audit-funding-vps-github-release.yml"
AUDIT_WORKFLOW_NAME = "Audit Immutable VPS Funding Evidence Release"
VALID_STATUS = "RELEASE_AND_INDEPENDENT_AUDIT_VERIFIED"
FAIL_STATES = frozenset({
    "MISSING_PUBLISHED_RELEASE", "INVALID_RELEASE", "AUDIT_MISSING",
    "AUDIT_PENDING", "AUDIT_FAILED", "UNASSESSED",
})


def _day(raw: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        raise ValueError("entry day must use canonical UTC YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("invalid UTC entry day") from exc
    if parsed.isoformat() != raw:
        raise ValueError("entry day is not canonical")
    return parsed


def _utc_now(now: Callable[[], datetime]) -> datetime:
    value = now()
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("reviewer clock must be timezone-aware")
    return value.astimezone(UTC)


def _eligible(day: date, instant: datetime) -> bool:
    deadline = datetime.combine(day, time.min, UTC) + timedelta(minutes=ENTRY_MINUTE)
    return FIRST_DAY <= day and instant >= deadline


def recent_completed_days(instant: datetime, *, count: int) -> list[date]:
    """Fixed-size UTC lookback; never check today's window before deadline."""
    if not 1 <= count <= 7:
        raise ValueError("lookback must be between 1 and 7 days")
    anchor = instant.date()
    if not _eligible(anchor, instant):
        anchor -= timedelta(days=1)
    return [
        d for i in range(count)
        if (d := anchor - timedelta(days=i)) >= FIRST_DAY
    ]


def _receipt(day: date, status: str, reason: str, **extra: Any) -> dict[str, Any]:
    if status != VALID_STATUS and status not in FAIL_STATES:
        raise ValueError("unknown watch result")
    return {
        "entry_market_date": day.isoformat(),
        "tag": f"funding-vps-{day.isoformat()}",
        "status": status,
        "reason": reason[:1024],
        "github_hosted_preentry_source_verified": False,
        "github_release_attestation_verified": False,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        **extra,
    }


def _api_failure(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"GitHub API returned HTTP {exc.response.status_code}"
    return type(exc).__name__


def _get_audits(client: httpx.Client, token: str) -> list[dict[str, Any]]:
    # A targeted workflow endpoint prevents older runs from being crowded out
    # by unrelated CI. GitHub Actions read permission is mandatory.
    resp = client.get(
        f"{API}/actions/workflows/{AUDIT_WORKFLOW}/runs",
        params={"event": "release", "per_page": 100},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict) or not isinstance(data.get("workflow_runs"), list):
        raise ValueError("invalid GitHub audit runs response")
    if len(data["workflow_runs"]) > 100:
        raise ValueError("GitHub returned too many audit runs")
    return data["workflow_runs"]


def _find_audit(
    audits: list[dict[str, Any]], tag: str, published: datetime,
) -> dict[str, Any] | None:
    relevant: list[dict[str, Any]] = []
    for run in audits:
        if not isinstance(run, dict):
            raise ValueError("invalid GitHub workflow-run item")
        if run.get("event") != "release" or run.get("head_branch") != tag:
            continue
        if run.get("name") != AUDIT_WORKFLOW_NAME or type(run.get("id")) is not int:
            continue
        at = run.get("created_at")
        if not isinstance(at, str):
            raise ValueError("release audit created_at missing")
        try:
            started = datetime.fromisoformat(at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("release audit created_at invalid") from exc
        if started.tzinfo is None or started.astimezone(UTC) < published:
            raise ValueError("release audit started before source publication")
        relevant.append(run)
    if not relevant:
        return None
    return max(relevant, key=lambda run: (run["created_at"], run.get("run_attempt", 1)))


def check_day(
    day: date, *, now: datetime, client: httpx.Client, audits: list[dict[str, Any]],
    verify: Callable[..., dict[str, Any]] = verify_release,
) -> dict[str, Any]:
    """Validate the *actual published release* and the exact release audit."""
    if not _eligible(day, now):
        return _receipt(day, "UNASSESSED", "before entry deadline or rollout date")
    tag = f"funding-vps-{day.isoformat()}"
    try:
        response = client.get(
            f"{API}/releases/tags/{tag}",
            headers={"Accept": "application/vnd.github+json"},
        )
        if response.status_code == 404:
            return _receipt(
                day, "MISSING_PUBLISHED_RELEASE",
                "no public published GitHub Release at or after UTC entry deadline",
            )
        response.raise_for_status()
        metadata = response.json()
        if not isinstance(metadata, dict) or metadata.get("tag_name") != tag:
            return _receipt(day, "INVALID_RELEASE", "wrong GitHub Release identity")
        # The original auditor independently re-fetches the Release,
        # checks source bytes and immutable GitHub server timing.
        validated = verify(day.isoformat(), client=client)
        if validated.get("status") != (
            "github_immutable_release_metadata_and_offline_replay_only"
        ) or validated.get("tag") != tag:
            return _receipt(day, "INVALID_RELEASE", "original source replay unverified")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 403, 429) or exc.response.status_code >= 500:
            return _receipt(day, "UNASSESSED", _api_failure(exc))
        return _receipt(day, "INVALID_RELEASE", _api_failure(exc))
    except httpx.RequestError as exc:
        return _receipt(day, "UNASSESSED", _api_failure(exc))
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return _receipt(day, "INVALID_RELEASE", str(exc))
    published_raw = validated["published_at"]
    published = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
    if published.tzinfo is None:
        return _receipt(day, "INVALID_RELEASE", "release publication timezone missing")
    try:
        run = _find_audit(audits, tag, published.astimezone(UTC))
    except (ValueError, TypeError) as exc:
        return _receipt(day, "UNASSESSED", str(exc))
    evidence = {
        "published_at": published_raw,
        "archive_sha256": validated["archive_sha256"],
        "regime": validated["regime"],
        "github_hosted_preentry_source_verified": True,
    }
    if run is None:
        return _receipt(day, "AUDIT_MISSING", "no matching release.published audit", **evidence)
    run_id = run["id"]
    evidence["audit_run_id"] = run_id
    evidence["audit_run_url"] = f"https://github.com/{REPO}/actions/runs/{run_id}"
    if run.get("status") != "completed":
        return _receipt(day, "AUDIT_PENDING", "independent Release audit not completed", **evidence)
    if run.get("conclusion") != "success":
        return _receipt(day, "AUDIT_FAILED", "independent Release audit did not succeed", **evidence)
    return _receipt(
        day, VALID_STATUS, "immutable original bytes and release.published audit verified",
        github_release_attestation_verified=True, **evidence,
    )


# Fixed research strata: Funding sign × trailing spot volatility (100bps).
# These labels are already emitted by the original-source replay auditor.
REGIME_STRATA = (
    "negative_low_volatility",
    "negative_high_volatility",
    "nonnegative_low_volatility",
    "nonnegative_high_volatility",
)


def summarize_audited_regimes(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Inventory audited GitHub-held prospective sources, never historical eligibility.

    A Release that exists without its matching successful independent audit
    remains unassessed. In particular, a regime attached to an AUDIT_FAILED
    result must NEVER be counted as a verified observation.
    """
    strata: dict[str, dict[str, Any]] = {
        regime: {"count": 0, "dates": []} for regime in REGIME_STRATA
    }
    non_audited: list[dict[str, str]] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid daily record")
        raw_day = record.get("entry_market_date")
        if not isinstance(raw_day, str):
            raise ValueError("daily record missing canonical UTC date")
        _day(raw_day)
        if raw_day in seen:
            raise ValueError("duplicate daily record in audited regime window")
        seen.add(raw_day)

        status = record.get("status")
        if status == VALID_STATUS:
            if (
                record.get("github_hosted_preentry_source_verified") is not True
                or record.get("github_release_attestation_verified") is not True
            ):
                raise ValueError("verified regime needs audited original GitHub source")
            regime = record.get("regime")
            if not isinstance(regime, str) or regime not in strata:
                raise ValueError("verified source has unknown Funding regime")
            strata[regime]["dates"].append(raw_day)
        elif status in FAIL_STATES:
            # Never use an unverified regime even if raw replay returned one.
            non_audited.append({"date": raw_day, "status": status})
        else:
            raise ValueError("unknown daily Release audit status")

    for value in strata.values():
        value["dates"].sort()
        value["count"] = len(value["dates"])
    non_audited.sort(key=lambda item: item["date"])
    audited_count = sum(value["count"] for value in strata.values())
    return {
        "status": "AUDITED_GITHUB_CUSTODY_ONLY" if not non_audited else "PARTIAL",
        "scope": "checked_utc_release_days_only",
        "regime_boundary": "existing_frozen_100bps",
        "checked_day_count": len(records),
        "github_audited_day_count": audited_count,
        "non_audited_days": non_audited,
        "strata": strata,
        "empty_strata": [name for name, value in strata.items() if value["count"] == 0],
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "market_wide_opportunity_arrival_rate": None,
    }


def watch(
    *, now: Callable[[], datetime], client: httpx.Client,
    token: str, days: int = 3, entry_day: str | None = None,
    verify: Callable[..., dict[str, Any]] = verify_release,
) -> dict[str, Any]:
    instant = _utc_now(now)
    targets = [_day(entry_day)] if entry_day is not None else recent_completed_days(
        instant, count=days
    )
    if not targets:
        return {
            "status": "UNASSESSED", "checked_at": instant.isoformat(),
            "reason": "no eligible future-day source window yet", "days": [],
            "point_in_time_publication_verified": False,
            "acquisition_approved": False, "promotion_approved": False,
        }
    try:
        audits = _get_audits(client, token)
    except (httpx.HTTPError, ValueError, TypeError, json.JSONDecodeError) as exc:
        audits = None
        failed_reason = _api_failure(exc)
    if audits is None:
        results = [_receipt(d, "UNASSESSED", failed_reason) for d in targets]
    else:
        results = [
            check_day(d, now=instant, client=client, audits=audits, verify=verify)
            for d in targets
        ]
    ok = bool(results) and all(rec["status"] == VALID_STATUS for rec in results)
    try:
        coverage = summarize_audited_regimes(results)
    except (ValueError, TypeError) as exc:
        # A contradictory or unknown source regime is an evidence error, not
        # a reason to silently omit an observation or claim healthy custody.
        ok = False
        coverage = {
            "status": "UNASSESSED",
            "reason": str(exc)[:256],
            "point_in_time_publication_verified": False,
            "acquisition_approved": False,
            "promotion_approved": False,
        }
    return {
        "status": "HEALTHY" if ok else "UNASSESSED",
        "regime_coverage": coverage,
        "checked_at": instant.isoformat(),
        "repo": REPO,
        "lookback_days": days,
        "days": results,
        "github_only_read_only_watch": True,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--entry-day", help="optional exact historical UTC day to audit")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not 1 <= args.days <= 7:
        parser.error("--days must be 1..7")
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        parser.error("a read-only GH_TOKEN is required")
    try:
        with httpx.Client(timeout=httpx.Timeout(12.0)) as client:
            result = watch(
                now=lambda: datetime.now(UTC), client=client, token=token,
                days=args.days, entry_day=args.entry_day,
            )
    except (ValueError, TypeError, httpx.HTTPError) as exc:
        result = {
            "status": "UNASSESSED", "reason": type(exc).__name__,
            "point_in_time_publication_verified": False,
            "acquisition_approved": False, "promotion_approved": False,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    if result.get("status") != "HEALTHY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
