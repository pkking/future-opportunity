"""Independent-host OFFLINE review of original VPS Funding ZIP + manifest.

An externally supplied digest is required, but this tool cannot independently
prove the witness was recorded before entry or that OKX published data then.
Never feed VPS-origin bytes to the GitHub Actions *schedule* provenance auditor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import zipfile
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any, Callable

from audit_funding_preentry_source_artifact import audit_zip

ORIGIN = "vps_systemd_local_only"
SOURCE_MEMBERS = (
    "raw-api-capture.json",
    "http-timing.json",
    "preentry-research-evidence.json",
)
COMMON_MANIFEST = frozenset({
    "schema_version", "origin", "started_at", "intended_utc_day",
    "status", "archive_sha256", "entry_market_date", "files",
    "github_attestation_verified", "exchange_signed",
    "point_in_time_publication_verified", "acquisition_approved",
    "promotion_approved",
})
SUCCESS_MANIFEST = COMMON_MANIFEST | frozenset({
    "raw_file_sha256", "canonical_source_sha256", "regime",
})
FAILURE_MANIFEST = COMMON_MANIFEST | frozenset({"reason"})
MAX_MANIFEST_BYTES = 65536
MAX_ORIGINAL_ZIP_BYTES = 5_000_000
MAX_ERROR_BYTES = 20000


def _hex_digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key in VPS receipt")
        obj[key] = value
    return obj


def _json_object(data: bytes, name: str) -> dict[str, Any]:
    try:
        value = json.loads(data, object_pairs_hook=_unique_fields)
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"invalid {name} JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _regular_file_bytes(path: Path, *, max_bytes: int, name: str) -> bytes:
    info = path.lstat()  # Reject links, including symlinks into other date trees.
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= max_bytes:
        raise ValueError(f"{name} must be a bounded ordinary file")
    payload = path.read_bytes()
    if len(payload) != info.st_size or len(payload) > max_bytes:
        raise ValueError(f"{name} changed during offline review")
    return payload


def _utc(value: Any, name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a UTC ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must have a timezone")
    return parsed.astimezone(UTC)


def _manifest_common(
    manifest: dict[str, Any], *, expected_day: str, digest: str,
) -> tuple[str, datetime]:
    state = manifest.get("status")
    if state not in ("local_replay_only", "UNASSESSED"):
        raise ValueError("VPS local receipt has unexpected state")
    expected_keys = SUCCESS_MANIFEST if state == "local_replay_only" else FAILURE_MANIFEST
    if set(manifest) != expected_keys:
        raise ValueError("VPS manifest has unexpected or missing fields")
    if (
        type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != 1
        or manifest["origin"] != ORIGIN
        or manifest["intended_utc_day"] != expected_day
        or manifest["archive_sha256"] != digest
        or any(manifest[key] is not False for key in (
            "github_attestation_verified", "exchange_signed",
            "point_in_time_publication_verified", "acquisition_approved",
            "promotion_approved",
        ))
    ):
        raise ValueError("VPS manifest origin, day, digest or approval mismatch")
    started = _utc(manifest["started_at"], "started_at")
    if started.date().isoformat() != expected_day:
        raise ValueError("VPS recorder did not start on expected UTC day")
    return state, started


def _audit_failure_archive(archive: Path, manifest: dict[str, Any]) -> None:
    if manifest["files"] != ["error.json"] or manifest["entry_market_date"] is not None:
        raise ValueError("failed VPS receipt must not claim any market observation")
    if not isinstance(manifest["reason"], str) or not 0 < len(manifest["reason"]) <= 2048:
        raise ValueError("failed VPS receipt requires a bounded reason")
    try:
        with zipfile.ZipFile(archive) as z:
            members = z.infolist()
            if len(members) != 1 or members[0].filename != "error.json":
                raise ValueError("failed VPS receipt must contain exactly error.json")
            member = members[0]
            if (
                member.is_dir()
                or member.flag_bits & 1
                or not 0 < member.file_size <= MAX_ERROR_BYTES
                or stat.S_IFMT(member.external_attr >> 16) not in (0, stat.S_IFREG)
            ):
                raise ValueError("unsafe VPS failure ZIP")
            error = _json_object(z.read(member), "VPS failure receipt")
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise ValueError("failed VPS receipt has invalid original ZIP") from exc
    expected = {
        "status", "reason", "error_type",
        "point_in_time_publication_verified",
        "acquisition_approved", "promotion_approved",
    }
    if (
        set(error) != expected or error["status"] != "UNASSESSED"
        or error["reason"] != manifest["reason"]
        or not isinstance(error["error_type"], str)
        or not 0 < len(error["error_type"]) <= 128
        or any(error[k] is not False for k in (
            "point_in_time_publication_verified",
            "acquisition_approved", "promotion_approved",
        ))
    ):
        raise ValueError("failed VPS ZIP receipt cannot claim a successful capture")


def audit_vps_receipt(
    manifest_path: Path,
    archive_path: Path,
    *, expected_zip_sha256: str, expected_entry_date: str,
    reviewed_at: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Review both ORIGINAL files with an independently *supplied* expected digest."""
    if not _hex_digest(expected_zip_sha256):
        raise ValueError("expected ZIP SHA-256 must be lowercase 64-hex")
    if not isinstance(expected_entry_date, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", expected_entry_date,
    ):
        raise ValueError("independently expected UTC entry date must be YYYY-MM-DD")
    try:
        date.fromisoformat(expected_entry_date)
    except ValueError as exc:
        raise ValueError("independently expected UTC entry date is invalid") from exc

    manifest_bytes = _regular_file_bytes(
        manifest_path, max_bytes=MAX_MANIFEST_BYTES, name="VPS manifest",
    )
    manifest = _json_object(manifest_bytes, "VPS manifest")
    archive_bytes = _regular_file_bytes(
        archive_path, max_bytes=MAX_ORIGINAL_ZIP_BYTES, name="original VPS ZIP",
    )
    digest = hashlib.sha256(archive_bytes).hexdigest()
    if digest != expected_zip_sha256:
        raise ValueError("independently supplied VPS original ZIP digest mismatch")
    state, started = _manifest_common(
        manifest, expected_day=expected_entry_date, digest=digest,
    )

    if state == "local_replay_only":
        if manifest["files"] != list(SOURCE_MEMBERS):
            raise ValueError("successful VPS manifest has incorrect original file list")
        if manifest["entry_market_date"] != expected_entry_date:
            raise ValueError("successful VPS manifest has wrong market UTC date")
        if not all(_hex_digest(manifest[k]) for k in (
            "raw_file_sha256", "canonical_source_sha256",
        )):
            raise ValueError("VPS manifest contains invalid source digests")
        if not isinstance(manifest["regime"], str) or not manifest["regime"]:
            raise ValueError("VPS manifest regime is invalid")
        midnight = datetime.combine(started.date(), time.min, tzinfo=UTC)
        if not midnight <= started < midnight.replace(minute=15):
            raise ValueError("successful VPS recorder started outside UTC entry window")
        replay = audit_zip(
            archive_path,
            expected_zip_sha256=digest,
            expected_entry_date=expected_entry_date,
        )
        for field in ("raw_file_sha256", "canonical_source_sha256", "regime"):
            if manifest[field] != replay[field]:
                raise ValueError(f"VPS manifest {field} disagrees with original source replay")
        status = "offline_vps_replay_only"
        entry_market_date: str | None = expected_entry_date
    else:
        _audit_failure_archive(archive_path, manifest)
        replay = None
        status = "failed_capture_unassessed"
        entry_market_date = None

    now = reviewed_at() if reviewed_at is not None else datetime.now(UTC)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("reviewer clock must be timezone-aware")
    return {
        "schema_version": 1,
        "status": status,
        "origin": ORIGIN,
        "intended_utc_day": expected_entry_date,
        "entry_market_date": entry_market_date,
        "vps_reported_started_at": started.isoformat(),
        "reviewed_at": now.astimezone(UTC).isoformat(),
        "review_time_is_capture_time": False,
        "original_zip_sha256": digest,
        "expected_digest_match": True,
        "expected_digest_origin_authenticated": False,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "raw_file_sha256": replay["raw_file_sha256"] if replay is not None else None,
        "canonical_source_sha256": (
            replay["canonical_source_sha256"] if replay is not None else None
        ),
        "regime": replay["regime"] if replay is not None else None,
        "source_authentication_status": "requires_independent_provenance_review",
        "github_attestation_verified": False,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--zip", dest="archive", type=Path, required=True)
    parser.add_argument("--expected-zip-sha256", required=True)
    parser.add_argument("--entry-date", required=True)
    parser.add_argument("--receipt-out", type=Path, help="new offline review receipt; never overwrite")
    args = parser.parse_args()
    result = audit_vps_receipt(
        args.manifest, args.archive,
        expected_zip_sha256=args.expected_zip_sha256,
        expected_entry_date=args.entry_date,
    )
    if args.receipt_out is not None:
        # Save a distinct observer's review result. It is NOT a trusted
        # independent as-of-collection timestamp or a source signature.
        with args.receipt_out.open("x", encoding="utf-8") as f:
            os.fchmod(f.fileno(), 0o600)
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
