"""Read-only scheduled Funding capture review: ZIP replay + GitHub identity proof.

Both the GitHub run metadata and the immutable artifact digest must be fetched
from the API independently of the downloaded ZIP. GitHub provenance is NOT an
exchange signature, a trustworthy source-response timestamp, or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from audit_funding_preentry_source_artifact import audit_zip
from wait_for_funding_preentry_window import target_midnight

ARTIFACT_NAME = "prospective-funding-preentry-source"
WORKFLOW_PATH = ".github/workflows/capture-funding-preentry-scheduled.yml"
MAX_SIZE = 5_000_000


def _identity(
    run: dict[str, Any], inventory: dict[str, Any], *,
    repository: str, run_id: int, source_sha: str,
) -> tuple[dict[str, Any], str, str]:
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("scheduled source commit must be a Git SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("scheduled source repository has invalid identity")
    if (
        run.get("id") != run_id
        or run.get("event") != "schedule"
        or run.get("run_attempt") != 1
        or run.get("head_sha") != source_sha
        or run.get("head_branch") != "main"
        or run.get("path") != WORKFLOW_PATH
        or not isinstance(run.get("head_repository"), dict)
        or run["head_repository"].get("full_name") != repository
    ):
        raise ValueError("scheduled source run identity, trigger or commit mismatch")
    try:
        triggered_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        if triggered_at.tzinfo is None:
            raise ValueError("scheduled trigger missing timezone")
        day = target_midnight(triggered_at.astimezone(UTC)).date().isoformat()
    except (TypeError, KeyError, AttributeError, ValueError) as exc:
        raise ValueError("scheduled trigger UTC time is invalid or missed") from exc
    if not isinstance(inventory, dict) or not isinstance(
        inventory.get("artifacts"), list
    ):
        raise ValueError("GitHub artifact inventory is missing")
    matches = [
        a for a in inventory["artifacts"]
        if isinstance(a, dict) and a.get("name") == ARTIFACT_NAME
    ]
    if len(matches) != 1:
        raise ValueError("scheduled run must own exactly one named original artifact")
    artifact = matches[0]
    belongs = artifact.get("workflow_run")
    if (
        artifact.get("expired") is not False
        or not isinstance(belongs, dict)
        or belongs.get("id") != run_id
        or belongs.get("head_sha") != source_sha
        or belongs.get("head_branch") != "main"
        or not isinstance(artifact.get("id"), int)
        or not isinstance(artifact.get("size_in_bytes"), int)
        or not 0 < artifact["size_in_bytes"] <= MAX_SIZE
    ):
        raise ValueError("scheduled artifact identity, size or availability invalid")
    digest = artifact.get("digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("GitHub artifact digest is missing or invalid")
    if artifact.get("name") != ARTIFACT_NAME:
        raise ValueError("scheduled source artifact name mismatch")
    return artifact, digest.removeprefix("sha256:"), day


def _error_receipt(archive_path: Path) -> dict[str, Any]:
    """A failed capture is one explicit error.json, never a successful zero."""
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if (
            len(members) != 1
            or members[0].filename != "error.json"
            or members[0].file_size > 50_000
            or members[0].is_dir()
        ):
            raise ValueError("failed scheduled capture must contain only error.json")
        try:
            data = json.loads(archive.read(members[0]))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("failed scheduled capture receipt is not JSON") from exc
    if (
        not isinstance(data, dict)
        or data.get("status") != "UNASSESSED"
        or data.get("point_in_time_publication_verified") is not False
        or data.get("acquisition_approved") is not False
        or data.get("promotion_approved") is not False
        or not isinstance(data.get("reason"), str)
        or not data["reason"]
    ):
        raise ValueError("failed scheduled capture receipt claims unsupported status")
    return {
        "status": "failed_capture_unassessed",
        "failure_reason": data["reason"][:300],
        "github_attestation_verified": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }


def verify_github_attestation(raw: bytes, *, repository: str, sha: str) -> dict[str, Any]:
    """Call official GitHub CLI and constrain signer workflow, main ref and SHA."""
    with tempfile.TemporaryDirectory(prefix="funding-source-review-") as directory:
        subject = Path(directory) / "raw-api-capture.json"
        subject.write_bytes(raw)
        try:
            process = subprocess.run(
                [
                    "gh", "attestation", "verify", str(subject),
                    "--repo", repository,
                    "--signer-workflow", f"{repository}/{WORKFLOW_PATH}",
                    "--source-ref", "refs/heads/main",
                    "--source-digest", sha,
                    "--format", "json",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            raise ValueError("GitHub signed raw-subject verification failed") from exc
    try:
        verified = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("GitHub attestation verification returned malformed JSON") from exc
    digest = hashlib.sha256(raw).hexdigest()
    if not isinstance(verified, list) or not verified or not any(
        isinstance(x, dict)
        and isinstance(x.get("verificationResult"), dict)
        and any(
            isinstance(subject, dict)
            and subject.get("digest", {}).get("sha256") == digest
            for subject in x["verificationResult"].get("statement", {}).get("subject", [])
        )
        for x in verified
    ):
        raise ValueError("GitHub attestation subject digest mismatch")
    return {"github_attestation_verified": True, "raw_file_sha256": digest}


def audit_scheduled_capture(
    archive_path: Path, *,
    run: dict[str, Any], inventory: dict[str, Any],
    repository: str, run_id: int, source_sha: str,
    capture_conclusion: str,
    verifier: Callable[..., dict[str, Any]] = verify_github_attestation,
) -> dict[str, Any]:
    """One actual run only; no historical backfill, capture, or promotion."""
    artifact, expected_sha256, day = _identity(
        run, inventory, repository=repository, run_id=run_id, source_sha=source_sha,
    )
    payload = archive_path.read_bytes()
    if not payload or len(payload) > MAX_SIZE:
        raise ValueError("original scheduled source ZIP is missing or oversized")
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("independent GitHub scheduled artifact digest mismatch")
    common: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "source_sha": source_sha,
        "artifact_id": artifact["id"],
        "entry_market_date": day,
        "original_zip_sha256": expected_sha256,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "source_authentication_status": "requires_independent_provenance_review",
        "acquisition_approved": False,
        "promotion_approved": False,
    }
    if capture_conclusion != "success":
        if capture_conclusion != "failure":
            raise ValueError("unapproved scheduled capture conclusion")
        return {**common, **_error_receipt(archive_path)}
    replay = audit_zip(
        archive_path, expected_zip_sha256=expected_sha256, expected_entry_date=day,
    )
    with zipfile.ZipFile(archive_path) as archive:
        raw = archive.read("raw-api-capture.json")
    attested = verifier(raw, repository=repository, sha=source_sha)
    if (
        not isinstance(attested, dict)
        or attested.get("github_attestation_verified") is not True
        or attested.get("raw_file_sha256") != replay["raw_file_sha256"]
    ):
        raise ValueError("GitHub raw-subject verification is incomplete")
    return {
        **common,
        "status": "offline_replay_and_github_provenance_verified_only",
        "github_attestation_verified": True,
        "raw_file_sha256": replay["raw_file_sha256"],
        "canonical_source_sha256": replay["canonical_source_sha256"],
        "source_record_sha256": replay["source_record_sha256"],
        "regime": replay["regime"],
        "note": (
            "GitHub-signed workflow source and internal replay verified, NOT "
            "exchange-signed data, independent source publication time or "
            "a historically promotable/acquisition-approved sample."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--run-metadata", type=Path, required=True)
    parser.add_argument("--artifact-metadata", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--capture-conclusion", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        archives = list(args.archive_dir.glob("*.zip"))
        if len(archives) != 1 or len(list(args.archive_dir.iterdir())) != 1:
            raise ValueError("expected exactly one original downloaded source ZIP")
        result = audit_scheduled_capture(
            archives[0], run=json.loads(args.run_metadata.read_text()),
            inventory=json.loads(args.artifact_metadata.read_text()),
            repository=args.repository, run_id=args.run_id,
            source_sha=args.source_sha, capture_conclusion=args.capture_conclusion,
        )
        (args.output_dir / "scheduled-evidence-review.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n"
        )
        print(json.dumps(result, sort_keys=True, indent=2))
    except Exception as exc:
        (args.output_dir / "error.json").write_text(
            json.dumps({
                "status": "UNASSESSED",
                "error_type": type(exc).__name__,
                "reason": str(exc),
                "github_attestation_verified": False,
                "point_in_time_publication_verified": False,
                "acquisition_approved": False,
                "promotion_approved": False,
            }, sort_keys=True, indent=2) + "\n"
        )
        raise


if __name__ == "__main__":
    main()
