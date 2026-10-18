"""Offline, fail-closed audit of a *prospective* Funding source Actions ZIP.

This only checks an originally downloaded archive's identity and internal
consistency. It does not attest an OKX publication time or permit promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

from future_opportunity.backtest.funding_asof_capture import validate_preentry_source

REQUIRED_MEMBERS = frozenset({
    "raw-api-capture.json",
    "http-timing.json",
    "preentry-research-evidence.json",
})
MAX_MEMBER_BYTES = 2_000_000


def audit_zip(
    archive_path: Path, *, expected_zip_sha256: str, expected_entry_date: str,
) -> dict[str, Any]:
    """Replay observed facts; do not assert independent timing or signatures."""
    if not re.fullmatch(r"[0-9a-f]{64}", expected_zip_sha256):
        raise ValueError("expected ZIP SHA-256 must be 64 lowercase hex digits")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", expected_entry_date):
        raise ValueError("expected entry date must be a UTC YYYY-MM-DD date")
    try:
        date.fromisoformat(expected_entry_date)
    except ValueError as exc:
        raise ValueError("expected entry date is invalid") from exc

    archive_bytes = archive_path.read_bytes()
    digest = hashlib.sha256(archive_bytes).hexdigest()
    if digest != expected_zip_sha256:
        raise ValueError("original prospective ZIP SHA-256 mismatch")

    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.infolist()
            if len(members) != len(REQUIRED_MEMBERS) or {
                member.filename for member in members
            } != REQUIRED_MEMBERS:
                raise ValueError("prospective ZIP must contain exactly three original files")
            if any(
                member.file_size > MAX_MEMBER_BYTES
                or member.is_dir()
                or member.flag_bits & 1
                or stat.S_IFMT(member.external_attr >> 16) not in (0, stat.S_IFREG)
                for member in members
            ):
                raise ValueError("prospective ZIP contains unsafe or oversized members")
            files = {member.filename: archive.read(member) for member in members}
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise ValueError("prospective ZIP is not a readable original artifact") from exc
    if any(len(content) > MAX_MEMBER_BYTES for content in files.values()):
        raise ValueError("prospective ZIP extracted content exceeds member size limit")

    try:
        raw = json.loads(files["raw-api-capture.json"])
        timing = json.loads(files["http-timing.json"])
        claimed = json.loads(files["preentry-research-evidence.json"])
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("prospective ZIP contains invalid JSON") from exc
    recomputed = validate_preentry_source(raw, timing)
    if claimed != recomputed:
        raise ValueError("prospective research evidence does not match source replay")
    if recomputed["entry_at"][:10] != expected_entry_date:
        raise ValueError("prospective entry date does not match independent expectation")
    if (
        recomputed["point_in_time_publication_verified"] is not False
        or recomputed["exchange_signed"] is not False
        or recomputed["acquisition_approved"] is not False
        or recomputed["promotion_approved"] is not False
    ):
        raise ValueError("source audit must not approve publication or promotion")

    return {
        "status": "offline_replay_verified_only",
        "entry_date": expected_entry_date,
        "archive_sha256": digest,
        "raw_file_sha256": hashlib.sha256(files["raw-api-capture.json"]).hexdigest(),
        "canonical_source_sha256": recomputed["raw_source_sha256"],
        "source_record_sha256": recomputed["source_record_sha256"],
        "regime": recomputed["regime"],
        "http_transactions_completed_before_entry": True,
        "github_attestation_verified": False,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "source_authentication_status": "requires_independent_provenance_review",
        "acquisition_approved": False,
        "promotion_approved": False,
        "note": (
            "This only verifies archive digest and internal replay. Independently "
            "verify GitHub/Sigstore attestation, run and clock evidence, and "
            "exchange publication separately. Do not backdate observed evidence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", dest="archive", type=Path, required=True)
    parser.add_argument("--expected-zip-sha256", required=True)
    parser.add_argument("--entry-date", required=True, help="independently expected UTC YYYY-MM-DD")
    args = parser.parse_args()
    print(json.dumps(audit_zip(
        args.archive,
        expected_zip_sha256=args.expected_zip_sha256,
        expected_entry_date=args.entry_date,
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
