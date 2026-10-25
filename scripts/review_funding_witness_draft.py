"""Offline-only Option-B witness candidate comparator. NOT an R2 trust verifier.

A self-declared observer identity, clock, SHA-256 or local receipt is NOT
independent evidence. This prototype checks source, timing and equality only;
actual observer signing and independently anchored timestamps are out of scope.
Never calls OKX/GitHub or upgrades historical source/acquisition status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from audit_vps_funding_capture import _json_object
from future_opportunity.backtest.funding_asof_capture import validate_preentry_source
from future_opportunity.backtest.funding_raw_feature_lineage import (
    FUNDING_ENDPOINT,
    FUNDING_INSTRUMENT,
    SPOT_ENDPOINT,
    SPOT_INSTRUMENT,
    reconstruct_funding_regime_features,
)

MAX_JSON_BYTES = 2_000_000
MAX_RECEIPT_BYTES = 16_384
MAX_DECLARED_CLOCK_UNCERTAINTY_MS = 1_000
SOURCE_QUERIES = {
    "funding": {"instId": FUNDING_INSTRUMENT, "limit": "400"},
    "spot": {"instId": SPOT_INSTRUMENT, "bar": "1Dutc", "limit": "100"},
}
SOURCE_ENDPOINTS = {"funding": FUNDING_ENDPOINT, "spot": SPOT_ENDPOINT}
OBSERVATION_FIELDS = frozenset({
    "endpoint", "query", "started_at", "received_at", "raw_sha256",
})
RECEIPT_FIELDS = frozenset({
    "schema_version", "entry_market_date", "entry_at", "observer_id",
    "collector_id", "observer_network", "collector_network",
    "clock_uncertainty_ms", "witness_recorded_at", "funding", "spot",
})


def _read_object(path: Path, *, limit: int, label: str) -> tuple[bytes, dict[str, Any]]:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
        raise ValueError(f"{label}: require bounded regular non-symlink file")
    content = path.read_bytes()
    if len(content) != info.st_size or len(content) > limit:
        raise ValueError(f"{label}: file changed or grew during review")
    return content, _json_object(content, label)


def _utc_time(raw: Any, label: str) -> datetime:
    if not isinstance(raw, str):
        raise ValueError(f"{label}: ISO timestamp string required")
    try:
        moment = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label}: invalid ISO timestamp") from exc
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError(f"{label}: timezone required")
    return moment.astimezone(UTC)


def _digest(raw: Any, label: str) -> None:
    if not isinstance(raw, str) or re.fullmatch(r"[a-f0-9]{64}", raw) is None:
        raise ValueError(f"{label}: lowercase SHA256 required")


def _candidate_capture(
    receipt: dict[str, Any],
    funding_body: bytes,
    spot_body: bytes,
) -> tuple[dict[str, Any], dict[str, str]]:
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_FIELDS:
        raise ValueError("observer receipt exact schema required")
    if type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1:
        raise ValueError("unsupported observer receipt schema")
    raw_day = receipt["entry_market_date"]
    if not isinstance(raw_day, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_day):
        raise ValueError("observer entry day must be canonical")
    try:
        day = date.fromisoformat(raw_day)
    except ValueError as exc:
        raise ValueError("observer entry day invalid") from exc
    if day.isoformat() != raw_day:
        raise ValueError("noncanonical UTC entry day")
    midnight = datetime.combine(day, time.min, UTC)
    entry = midnight + timedelta(minutes=15)
    if _utc_time(receipt["entry_at"], "entry_at") != entry:
        raise ValueError("expected pre-entry UTC 00:15 boundary")

    # Merely DECLARED administrative separation. No cryptographic proof.
    identity_fields = (
        "observer_id", "collector_id", "observer_network", "collector_network",
    )
    if any(
        not isinstance(receipt[f], str)
        or not receipt[f].strip()
        or len(receipt[f]) > 128
        for f in identity_fields
    ):
        raise ValueError("bounded declared observer/collector identities required")
    if (
        receipt["observer_id"] == receipt["collector_id"]
        or receipt["observer_network"] == receipt["collector_network"]
    ):
        raise ValueError("observer must declare distinct collector owner/network")

    error_ms = receipt["clock_uncertainty_ms"]
    if (
        type(error_ms) is not int
        or not 0 <= error_ms <= MAX_DECLARED_CLOCK_UNCERTAINTY_MS
    ):
        raise ValueError("declared clock uncertainty exceeds offline draft bound")
    uncertainty = timedelta(milliseconds=error_ms)
    receipt_at = _utc_time(receipt["witness_recorded_at"], "witness_recorded_at")
    if not midnight + uncertainty <= receipt_at or receipt_at + uncertainty >= entry:
        raise ValueError("witness receipt time not safely before entry")

    times: list[datetime] = []
    for kind, raw_body in (("funding", funding_body), ("spot", spot_body)):
        item = receipt[kind]
        if not isinstance(item, dict) or set(item) != OBSERVATION_FIELDS:
            raise ValueError(f"{kind}: exact observer request schema required")
        if item["endpoint"] != SOURCE_ENDPOINTS[kind] or item["query"] != SOURCE_QUERIES[kind]:
            raise ValueError(f"{kind}: incorrect official public endpoint/query")
        _digest(item["raw_sha256"], kind + " raw_sha256")
        if hashlib.sha256(raw_body).hexdigest() != item["raw_sha256"]:
            raise ValueError(f"{kind}: original response body SHA256 mismatch")
        started = _utc_time(item["started_at"], kind + " started_at")
        received = _utc_time(item["received_at"], kind + " received_at")
        times.extend((started, received))
    if not (
        midnight + uncertainty <= times[0] <= times[1]
        <= times[2] <= times[3] <= receipt_at
        and receipt_at + uncertainty < entry
    ):
        raise ValueError("observer HTTP/receipt times invalid or past entry with clock bound")

    funding = _json_object(funding_body, "witness funding original response")
    spot = _json_object(spot_body, "witness spot original response")
    capture = {
        "schema_version": 1,
        "captured_at": receipt_at.isoformat(),
        "start_date": raw_day,
        "end_date": raw_day,
        "seed": "independent-witness-draft-outcome-blind",
        "requested_per_regime": 1,
        "pinned_market_dates": [],
        "funding_query": SOURCE_QUERIES["funding"],
        "funding_response": funding,
        "spot_query": SOURCE_QUERIES["spot"],
        "spot_response": spot,
    }
    timing = {
        "entry_at": entry.isoformat(),
        "funding_request_started_at": times[0].isoformat(),
        "funding_response_received_at": times[1].isoformat(),
        "spot_request_started_at": times[2].isoformat(),
        "spot_response_received_at": times[3].isoformat(),
    }
    return capture, timing


def review_draft(
    receipt_path: Path,
    funding_path: Path,
    spot_path: Path,
    r1_source_path: Path,
) -> dict[str, Any]:
    """Check candidate replay only. Even positive output has no R2 trust level."""
    result: dict[str, Any] = {
        "status": "UNASSESSED",
        "scope": "offline_unattested_independent_witness_candidate_only",
        "observer_identity_attested": False,
        "trusted_time_attested": False,
        "r1_source_custody_verified_here": False,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "market_wide_opportunity_arrival_rate": None,
    }
    try:
        _, receipt = _read_object(
            receipt_path, limit=MAX_RECEIPT_BYTES, label="observer receipt"
        )
        funding_bytes, _ = _read_object(
            funding_path, limit=MAX_JSON_BYTES, label="witness funding body"
        )
        spot_bytes, _ = _read_object(
            spot_path, limit=MAX_JSON_BYTES, label="witness spot body"
        )
        _, r1_source = _read_object(
            r1_source_path, limit=MAX_JSON_BYTES, label="R1 original raw JSON"
        )
        candidate, timing = _candidate_capture(receipt, funding_bytes, spot_bytes)
        if (
            r1_source.get("start_date") != candidate["start_date"]
            or r1_source.get("end_date") != candidate["end_date"]
        ):
            raise ValueError("candidate and R1 source UTC entry day differ")
        checked = validate_preentry_source(candidate, timing)
        r1_replay = reconstruct_funding_regime_features(r1_source)
        observed = r1_replay["planner_input"]["observations"]
        if r1_replay["missing_days"] or len(observed) != 1:
            raise ValueError("R1 source does not contain one complete entry observation")
        r1_input = observed[0]
        candidate_replay = reconstruct_funding_regime_features(candidate)
        candidate_input = candidate_replay["planner_input"]["observations"][0]
        # Match all outcome-blind feature source rows: the same settled Funding
        # event plus the same eight completed daily candles, including close.
        # Any upstream cache divergence remains an unapproved conflict.
        same_records = (
            r1_input["source_record_id"] == candidate_input["source_record_id"]
            and r1_input["source_record_sha256"] == candidate_input["source_record_sha256"]
            and r1_input["entry_at"] == candidate_input["entry_at"]
            and checked["source_record_sha256"] == candidate_input["source_record_sha256"]
        )
        result.update({
            "entry_market_date": candidate["start_date"],
            "funding_body_sha256": hashlib.sha256(funding_bytes).hexdigest(),
            "spot_body_sha256": hashlib.sha256(spot_bytes).hexdigest(),
            "source_record_id": candidate_input["source_record_id"],
            "candidate_source_record_sha256": candidate_input["source_record_sha256"],
            "r1_source_record_sha256": r1_input["source_record_sha256"],
            "declared_timing_and_source_internally_consistent": True,
            "source_record_match": same_records,
            "status": (
                "CANDIDATE_MATCH_UNATTESTED"
                if same_records else "CANDIDATE_CONFLICT_UNATTESTED"
            ),
        })
    except (ValueError, KeyError, TypeError, OSError) as exc:
        # Do not relay potentially secret raw payload content into the report.
        result["reason"] = type(exc).__name__
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--funding-body", type=Path, required=True)
    parser.add_argument("--spot-body", type=Path, required=True)
    parser.add_argument("--r1-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = review_draft(
        args.receipt, args.funding_body, args.spot_body, args.r1_source
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "CANDIDATE_MATCH_UNATTESTED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
