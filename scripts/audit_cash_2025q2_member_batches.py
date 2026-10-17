"""Independently audit all nine immutable Actions ZIPs for exact Cash Q2 source members.

No HTTP access, no profitability calculation and no sample selection. Requires an
exact artifact manifest and original independently audited source-catalog ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from audit_cash_2025q2_source_calendar import audit, expected_dates, extract_zip
from probe_cash_2025q2_members import FUTURE_ID, dates_for_batch
from future_opportunity.backtest.cash_discovery import future_ids_from_archive_members

_HEX = re.compile(r"^[0-9a-f]{64}$")
PINNED_CATALOG_SHA = "1b9a4adcb7035ca4abb70e5a9f1823dc3a71f5e9849070ce59c493df205b57ae"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def sha_ok(value: Any) -> bool:
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def audit_batch_zip(archive_path: Path, expected_digest: str, index: int) -> dict[str, Any]:
    require(sha_ok(expected_digest), "bad Actions batch artifact SHA-256")
    require(hashlib.sha256(archive_path.read_bytes()).hexdigest() == expected_digest,
            "Actions batch artifact ZIP SHA-256 mismatch")
    with zipfile.ZipFile(archive_path) as archive:
        paths = archive.namelist()
        require(paths == [f"member-batch-{index:02d}.json"],
                "batch artifact must contain exactly the expected research report")
        require(0 < archive.infolist()[0].file_size < 250_000,
                "batch report size exceeds fixed limit")
        payload = json.loads(archive.read(paths[0]))
    require(isinstance(payload, dict), "batch research report must be object")
    return payload


def audit_population(
    source_zip: Path, manifest: dict[str, Any], artifact_dir: Path
) -> dict[str, Any]:
    require(isinstance(manifest, dict)
            and set(manifest) == {"schema_version", "evidence_type",
                                  "source_catalog_run", "source_catalog_artifact_id",
                                  "source_catalog_sha256", "member_source_run",
                                  "member_source_head_sha", "batches"},
            "member-census artifact manifest schema mismatch")
    require(manifest["schema_version"] == 1
            and manifest["evidence_type"] == "cash_2025q2_exact_member_artifacts_manifest"
            and manifest["source_catalog_run"] == "39038071038"
            and manifest["source_catalog_artifact_id"] == "12103210971"
            and manifest["source_catalog_sha256"] == PINNED_CATALOG_SHA
            and type(manifest["member_source_run"]) is str
            and manifest["member_source_run"].isdigit()
            and isinstance(manifest["member_source_head_sha"], str)
            and bool(re.fullmatch("[0-9a-f]{40}", manifest["member_source_head_sha"])),
            "unknown source run, sha or preregistered catalog")
    summary = audit(source_zip, manifest["source_catalog_sha256"])
    require(summary["verified_calendar_dates"] == 90, "source catalog missing dates")
    catalog, _ = extract_zip(source_zip, manifest["source_catalog_sha256"])
    batches = manifest["batches"]
    require(isinstance(batches, list) and len(batches) == 9,
            "all 9 complete member source batches required")
    observations: list[dict[str, Any]] = []
    for index, item in enumerate(batches):
        require(isinstance(item, dict)
                and set(item) == {"batch_index", "artifact_id", "artifact_name", "zip_sha256"}
                and item["batch_index"] == index and type(item["artifact_id"]) is int
                and item["artifact_id"] > 0
                and item["artifact_name"] == f"cash-2025q2-exact-members-batch-{index}"
                and sha_ok(item["zip_sha256"]), "batch identity or Actions SHA mismatch")
        path = artifact_dir / f"{item['artifact_name']}.zip"
        batch = audit_batch_zip(path, item["zip_sha256"], index)
        require(batch.get("schema_version") == 1
                and batch.get("evidence_type") == "cash_2025q2_exact_futures_member_population_batch"
                and batch.get("future_id") == FUTURE_ID
                and batch.get("source_zip_sha256") == PINNED_CATALOG_SHA
                and batch.get("batch_index") == index
                and batch.get("calendar_dates") == list(dates_for_batch(index))
                and batch.get("research_only") is True
                and batch.get("outcome_blind") is True
                and batch.get("l2_orderbook_verified") is False
                and batch.get("sample_selection_frozen") is False
                and batch.get("economic_returns_evaluated") is False
                and batch.get("acquisition_approved") is False
                and batch.get("promotion_approved") is False,
                "batch source identity or safety invariant failed")
        rows = batch.get("observations")
        require(isinstance(rows, list) and len(rows) == 10
                and [row.get("market_date") for row in rows] == list(dates_for_batch(index)),
                "incomplete or reordered batch dates")
        counts = {s: 0 for s in ("identity_verified", "unavailable", "ambiguous", "error")}
        for row in rows:
            day = row["market_date"]
            expected = catalog[day + "/FUTURES"]
            official = expected["response"]["data"][0]["details"][0]["groupDetails"][0]
            require(row.get("future_id") == FUTURE_ID
                    and row.get("catalog_response_sha256") == expected["sha256"]
                    and row.get("official_archive_url") == official["url"]
                    and row.get("l2_orderbook_verified") is False
                    and row.get("economic_returns_evaluated") is False
                    and row.get("acquisition_approved") is False
                    and row.get("promotion_approved") is False
                    and row.get("member_status") in counts,
                    "source archive identity, date or governance mismatch")
            status = row["member_status"]
            counts[status] += 1
            if status == "error":
                require(row.get("member_identity_verified") is False
                        and isinstance(row.get("error_type"), str), "malformed source error")
            else:
                members = row.get("archive_members")
                require(isinstance(members, list)
                        and members == sorted(set(members)) and bool(members),
                        "missing or duplicate immutable member identities")
                ids = future_ids_from_archive_members(
                    members, expected_market_date=day
                )
                exact = f"{FUTURE_ID}-L2orderbook-400lv-{day}.data"
                number = members.count(exact)
                require(list(ids) == row.get("member_instrument_ids")
                        and number == row.get("matching_exact_contract_member_count")
                        and row.get("exact_contract_member") == (exact if number == 1 else None)
                        and row.get("member_identity_verified") is (status == "identity_verified")
                        and (status == "identity_verified") == (number == 1)
                        and (status == "unavailable") == (number == 0)
                        and status != "ambiguous"
                        and sha_ok(row.get("archive_sha256"))
                        and type(row.get("archive_downloaded_bytes")) is int
                        and 0 < row["archive_downloaded_bytes"] <= 512 * 1024 * 1024,
                        "member identities and immutable source archive hashes disagree")
            observations.append(row)
        require(batch.get("status_counts") == counts
                and batch.get("complete") is (counts["error"] == 0),
                "batch classification/counts inconsistent")
    days = expected_dates()
    require(len(observations) == 90
            and [x["market_date"] for x in observations] == list(days),
            "complete source population coverage failed")
    counts = {s: sum(x["member_status"] == s for x in observations)
              for s in ("identity_verified", "unavailable", "ambiguous", "error")}
    require(counts["error"] == 0 and counts["ambiguous"] == 0,
            "source population has unresolved error/ambiguity, cannot freeze")
    eligible = [x["market_date"] for x in observations
                if x["member_status"] == "identity_verified"]
    excluded = [x["market_date"] for x in observations
                if x["member_status"] == "unavailable"]
    return {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_exact_contract_member_population_offline_audit",
        "future_id": FUTURE_ID,
        "source_catalog_sha256": PINNED_CATALOG_SHA,
        "member_source_run": manifest["member_source_run"],
        "member_source_head_sha": manifest["member_source_head_sha"],
        "counts": counts,
        "frozen_calendar_dates": list(days),
        "verified_member_available_dates": eligible,
        "source_unavailable_dates": excluded,
        "complete_member_population_verified": True,
        "sample_selection_frozen": False,
        "l2_orderbook_verified": False,
        "economics_evaluated": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_population(
        args.source_zip, json.loads(args.manifest.read_text()), args.artifact_dir
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"counts": result["counts"], "complete": True,
                      "sample_selection_frozen": False}, sort_keys=True))


if __name__ == "__main__":
    main()
