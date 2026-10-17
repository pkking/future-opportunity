"""Offline, fail-closed audit of a pre-registered Cash Q2 source-calendar ZIP.

Verifies source API payload integrity and complete archive catalog lineage;
it does NOT establish presence of BTC-USDT-250627 inside FUTURES chain
archives, sampled L2 order books, or suitability for corpus promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

START = date(2025, 3, 29)
END = date(2025, 6, 26)
EXPECTED_FILES = frozenset({"catalog-raw-api-capture.json", "source-calendar-report.json"})


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def expected_dates() -> tuple[str, ...]:
    require((END - START).days == 89, "frozen source-calendar day count drift")
    return tuple((START + timedelta(days=i)).isoformat() for i in range(90))


def extract_zip(zip_path: Path, expected_sha256: str) -> tuple[dict[str, Any], dict[str, Any]]:
    require(len(expected_sha256) == 64 and all(c in "0123456789abcdef" for c in expected_sha256),
            "expected ZIP SHA-256 must be lowercase hexadecimal")
    require(hashlib.sha256(zip_path.read_bytes()).hexdigest() == expected_sha256,
            "Actions ZIP digest differs from independently recorded SHA-256")
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        require(len(names) == 2 and set(names) == EXPECTED_FILES,
                "archive must contain exactly the two original source reports")
        # Bounded size and file-type check; do not extract untrusted paths.
        require(all(0 < f.file_size <= 8_000_000 and not f.is_dir()
                    for f in archive.infolist()), "source report size/type invalid")
        raw = json.loads(archive.read("catalog-raw-api-capture.json"))
        report = json.loads(archive.read("source-calendar-report.json"))
    require(isinstance(raw, dict) and isinstance(report, dict), "source reports must be objects")
    return raw, report


def checked_catalog(payload: Any, day: str, kind: str) -> str:
    """Validate this exact official module-4 source snapshot, not contract membership."""
    require(isinstance(payload, dict) and payload.get("code") == "0", "invalid official response")
    entries = payload.get("data")
    require(isinstance(entries, list) and len(entries) == 1, "ambiguous/missing catalog response")
    item = entries[0]
    detail = item.get("details") if isinstance(item, dict) else None
    require(item.get("dateAggrType") == "daily" and isinstance(detail, list) and len(detail) == 1,
            "official catalog day/shape mismatch")
    record = detail[0]
    timestamp = str(int(datetime.combine(date.fromisoformat(day), datetime.min.time(), tzinfo=UTC).timestamp() * 1000))
    require(record.get("instType") == kind and record.get("dateRangeStart") == timestamp
            and record.get("dateRangeEnd") == timestamp, "catalog instrument/date mismatch")
    if kind == "FUTURES":
        require(record.get("instFamily") == "BTC-USDT" and record.get("instId") == "",
                "FUTURES catalog must identify the family, not claim exact contract")
        filename = f"BTC-USDT-futureschain-L2orderbook-400lv-{day}.tar.gz"
    else:
        require(record.get("instId") == "BTC-USDT" and record.get("instFamily") == "",
                "SPOT catalog source identity mismatch")
        filename = f"BTC-USDT-L2orderbook-400lv-{day}.tar.gz"
    groups = record.get("groupDetails")
    require(isinstance(groups, list) and len(groups) == 1, "missing/ambiguous archive group")
    actual = groups[0]
    require(actual.get("dateTs") == timestamp and actual.get("filename") == filename,
            "archive filename or date differs from official catalog query")
    remote = urlsplit(actual.get("url", ""))
    require(remote.scheme == "https" and remote.netloc == "static.okx.com"
            and remote.path.endswith("/" + day.replace("-", "") + "/" + filename)
            and not remote.query and not remote.fragment, "unexpected archive URL")
    return filename


def audit(zip_path: Path, expected_sha256: str) -> dict[str, Any]:
    raw, report = extract_zip(zip_path, expected_sha256)
    days = expected_dates()
    keys = {f"{day}/{kind}" for day in days for kind in ("FUTURES", "SPOT")}
    require(set(raw) == keys, "source response set must cover exact frozen 90-day/180-call population")
    require(report.get("schema_version") == 1
            and report.get("evidence_type") == "cash_2025q2_retrospective_daily_catalog_population",
            "source report kind mismatch")
    original_rows = report.get("observations")
    require(isinstance(original_rows, list) and len(original_rows) == 90,
            "report must contain exactly 90 observations")
    checked_rows = []
    for day, row in zip(days, original_rows, strict=True):
        require(isinstance(row, dict) and set(row) == {"market_date", "futures", "spot"}
                and row["market_date"] == day, "report row/date mismatch")
        for kind in ("FUTURES", "SPOT"):
            item = raw[f"{day}/{kind}"]
            require(isinstance(item, dict) and set(item) == {"query", "response", "sha256"},
                    "raw API snapshot schema mismatch")
            ts = str(int(datetime.combine(date.fromisoformat(day), datetime.min.time(), tzinfo=UTC).timestamp() * 1000))
            query = {"module": "4", "instType": kind, "dateAggrType": "daily", "begin": ts, "end": ts}
            if kind == "FUTURES":
                query["instFamilyList"] = "BTC-USDT"
            else:
                query["instIdList"] = "BTC-USDT"
            require(item["query"] == query, "raw API query does not match frozen date/source")
            require(item["sha256"] == canonical_sha256(item["response"]), "raw API response SHA-256 mismatch")
            filename = checked_catalog(item["response"], day, kind)
            observed = row[kind.lower()]
            require(observed == {
                "status": "unique_catalog_archive_only", "candidate_count": 1,
                "archive_filename": filename,
                "contract_member_inside_futures_archive_verified": False,
                "sampled_book_verified": False,
                "response_sha256": item["sha256"],
            }, "report observation differs from raw official response")
        checked_rows.append(row)
    require(report.get("requested_calendar_days") == 90
            and report.get("source_catalog_days") == 90
            and report.get("paired_catalog_day_count") == 90
            and report.get("paired_catalog_dates") == list(days)
            and report.get("query_error_days") == []
            and report.get("source_population_complete") is True,
            "calendar report counts or availability disagree with source evidence")
    for field, expected in {
        "research_only": True, "acquisition_approved": False,
        "promotion_approved": False, "historical_selection_frozen": False,
        "sampled_economic_returns_inspected": False,
        "futures_member_identified_per_candidate_day": False,
        "l2_sampled_per_candidate_day": False,
    }.items():
        require(report.get(field) is expected, "source study non-promotion invariants changed: " + field)
    require(set(report) == {
        "schema_version", "evidence_type", "requested_calendar_days", "source_catalog_days",
        "paired_catalog_day_count", "paired_catalog_dates", "query_error_days",
        "source_population_complete", "futures_member_identified_per_candidate_day",
        "l2_sampled_per_candidate_day", "historical_selection_frozen",
        "sampled_economic_returns_inspected", "research_only", "acquisition_approved",
        "promotion_approved", "observations",
    }, "source report carries unexpected fields")
    return {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_source_calendar_independent_offline_audit",
        "actions_zip_sha256": expected_sha256,
        "verified_calendar_dates": len(checked_rows),
        "verified_raw_api_responses": len(keys),
        "paired_family_catalog_days": 90,
        "exact_future_contract_membership_verified": False,
        "sampled_l2_verified_for_population": False,
        "historical_sample_frozen": False,
        "economic_outcomes_evaluated": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "research_only": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-zip", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.artifact_zip, args.expected_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
