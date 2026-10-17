"""Outcome-blind, source-bound BTC-USDT-250627 member census for all 90 frozen days.

This job verifies whether an exact .data member exists in each dated official
FUTURES family-chain archive. It NEVER evaluates prices, L2, trades or returns.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from audit_cash_2025q2_source_calendar import audit, expected_dates, extract_zip
from future_opportunity.backtest.cash_discovery import future_ids_from_archive_members

FUTURE_ID = "BTC-USDT-250627"
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
BATCH_DAYS = 10
BATCH_COUNT = 9


def dates_for_batch(batch: int) -> tuple[str, ...]:
    if not isinstance(batch, int) or not 0 <= batch < BATCH_COUNT:
        raise ValueError("batch index must be 0..8")
    days = expected_dates()
    assert len(days) == BATCH_DAYS * BATCH_COUNT
    return days[batch * BATCH_DAYS:(batch + 1) * BATCH_DAYS]


def verify_members(path: Path, market_date: str) -> dict[str, Any]:
    """Inspect only archive member identities; never extract order book bytes."""
    date.fromisoformat(market_date)
    with tarfile.open(path, "r:gz") as archive:
        original = [x.name for x in archive.getmembers()
                    if x.isfile() and x.name.endswith(".data")]
    basenames = [name.rsplit("/", 1)[-1] for name in original]
    if not basenames or len(basenames) != len(set(basenames)):
        raise ValueError("empty or duplicate .data member list")
    found = future_ids_from_archive_members(
        tuple(basenames), expected_market_date=market_date
    )
    exact = [n for n in basenames if n.startswith(FUTURE_ID + "-L2orderbook-")]
    result = {
        "archive_members": sorted(basenames),
        "member_instrument_ids": list(found),
        "matching_exact_contract_member_count": len(exact),
        "exact_contract_member": exact[0] if len(exact) == 1 else None,
        "member_status": (
            "identity_verified" if len(exact) == 1
            else "unavailable" if not exact else "ambiguous"
        ),
    }
    return result


def source_for_date(raw: dict[str, Any], market_date: str) -> tuple[str, str]:
    """Read only the already-audited immutable official catalog response."""
    evidence = raw[market_date + "/FUTURES"]
    detail = evidence["response"]["data"][0]["details"][0]
    archive = detail["groupDetails"][0]
    return str(archive["url"]), str(evidence["sha256"])


def stream_archive(client: httpx.Client, url: str, path: Path) -> tuple[str, int]:
    """Bound downloaded compressed bytes, hash the complete original archive."""
    h = hashlib.sha256()
    count = 0
    with client.stream("GET", url) as response:
        response.raise_for_status()
        length = response.headers.get("content-length")
        if length is not None and int(length) > MAX_ARCHIVE_BYTES:
            raise ValueError("declared archive exceeds fixed 512MiB cap")
        with path.open("wb") as dest:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                count += len(chunk)
                if count > MAX_ARCHIVE_BYTES:
                    raise ValueError("downloaded archive exceeds fixed 512MiB cap")
                dest.write(chunk)
                h.update(chunk)
    if count == 0:
        raise ValueError("empty official source archive")
    return h.hexdigest(), count


def inspect_day(
    client: httpx.Client, market_date: str, raw: dict[str, Any]
) -> dict[str, Any]:
    url, catalog_sha = source_for_date(raw, market_date)
    result: dict[str, Any] = {
        "market_date": market_date,
        "future_id": FUTURE_ID,
        "catalog_response_sha256": catalog_sha,
        "official_archive_url": url,
        "archive_sha256": None,
        "archive_downloaded_bytes": None,
        "member_status": "error",
        "member_identity_verified": False,
        "l2_orderbook_verified": False,
        "economic_returns_evaluated": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }
    try:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "source.tar.gz"
            digest, size = stream_archive(client, url, archive_path)
            result["archive_sha256"] = digest
            result["archive_downloaded_bytes"] = size
            member = verify_members(archive_path, market_date)
            result.update(member)
            result["member_identity_verified"] = member["member_status"] == "identity_verified"
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            httpx.HTTPError, tarfile.TarError) as exc:
        result["member_status"] = "error"
        result["error_type"] = type(exc).__name__
        result["member_identity_verified"] = False
    return result


def census_batch(
    client: httpx.Client, raw: dict[str, Any], batch: int, *,
    checkpoint: Path | None = None, source_zip_sha256: str,
) -> dict[str, Any]:
    days = dates_for_batch(batch)
    items = []
    for day in days:
        items.append(inspect_day(client, day, raw))
        if checkpoint is not None:
            partial = {"batch_index": batch, "source_zip_sha256": source_zip_sha256,
                       "complete": False, "observations": items}
            checkpoint.write_text(json.dumps(partial, indent=2, sort_keys=True) + "\n")
    statuses = {k: sum(x["member_status"] == k for x in items)
                for k in ("identity_verified", "unavailable", "ambiguous", "error")}
    return {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_exact_futures_member_population_batch",
        "future_id": FUTURE_ID,
        "source_zip_sha256": source_zip_sha256,
        "batch_index": batch,
        "calendar_dates": list(days),
        "complete": all(x["member_status"] != "error" for x in items),
        "status_counts": statuses,
        "research_only": True,
        "outcome_blind": True,
        "l2_orderbook_verified": False,
        "sample_selection_frozen": False,
        "economic_returns_evaluated": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "observations": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--batch-index", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    dates_for_batch(args.batch_index)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Full fail-closed verification of 90 days and 180 official API response
    # hashes is mandatory before trusting *any* FUTURES archive URL.
    evidence = audit(args.source_zip, args.source_sha256)
    assert evidence["verified_calendar_dates"] == 90
    raw, _ = extract_zip(args.source_zip, args.source_sha256)
    path = args.output_dir / f"member-batch-{args.batch_index:02d}.json"
    with httpx.Client(
        timeout=httpx.Timeout(connect=30, read=120, write=30, pool=30),
        follow_redirects=False,
    ) as client:
        report = census_batch(client, raw, args.batch_index,
                              checkpoint=path, source_zip_sha256=args.source_sha256)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"batch": args.batch_index,
                      "status_counts": report["status_counts"],
                      "complete": report["complete"]}, sort_keys=True))
    if not report["complete"]:
        raise RuntimeError("member population batch has source errors; fail closed")


if __name__ == "__main__":
    main()
