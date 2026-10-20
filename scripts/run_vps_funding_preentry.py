"""VPS systemd one-shot Funding source recorder; local evidence only, never trading.

Uses the existing prospective OKX read-only collector and offline replay.
A VPS clock, local checksum or systemd timer cannot authenticate when OKX
published the source. No GitHub credential/attestation is used or claimed.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
import tempfile
import zipfile
from datetime import UTC, datetime, time as clock_time, timedelta
from pathlib import Path
from typing import Any, Callable

from audit_funding_preentry_source_artifact import audit_zip
from capture_funding_preentry_source import capture_today

SOURCE_FILES = (
    "raw-api-capture.json",
    "http-timing.json",
    "preentry-research-evidence.json",
)
MAX_SOURCE_BYTES = 2_000_000


NTP_SYNC_MARKER = Path("/run/systemd/timesync/synchronized")
# systemd-timesyncd normally polls no less often than every 2048 seconds.
# Two hours allows brief outages while rejecting a long-stale sync marker.
MAX_NTP_SYNC_AGE_SECONDS = 2 * 60 * 60


def ntp_is_synchronized(
    *, marker: Path = NTP_SYNC_MARKER,
    now: Callable[[], datetime] | None = None,
) -> bool:
    """Require a recent systemd-timesyncd sync with no sandboxed D-Bus call.

    /run is volatile across boots. The marker is touched when timesyncd
    successfully synchronizes; a stale marker is not ongoing clock proof.
    This local guard is not a trusted UTC timestamp or exchange signature.
    """
    try:
        details = marker.lstat()  # Reject symlinks rather than following them.
        if not stat.S_ISREG(details.st_mode):
            return False
        current = now() if now is not None else datetime.now(UTC)
        if current.tzinfo is None:
            return False
        age = current.astimezone(UTC).timestamp() - details.st_mtime
        return 0 <= age <= MAX_NTP_SYNC_AGE_SECONDS
    except (OSError, ValueError, OverflowError):
        # Missing/unreadable marker, invalid clock or stat -> no source GET.
        return False

def _persist_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    path.chmod(0o600)


def _write_archive(path: Path, contents: Path, names: tuple[str, ...]) -> str:
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            source = contents / name
            if source.is_symlink() or not source.is_file():
                raise ValueError("local collector missing ordinary source file")
            if source.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError("local collector source file is oversized")
            archive.write(source, arcname=name)
    path.chmod(0o600)
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    return digest


def collect_once(
    state_dir: Path, *,
    now: Callable[[], datetime] | None = None,
    synced: Callable[[], bool] = ntp_is_synchronized,
    collector: Callable[[Path], dict[str, Any]] = capture_today,
    replay: Callable[..., dict[str, Any]] = audit_zip,
) -> dict[str, Any]:
    """Create exactly one irreversible local daily receipt. No retries/backfill."""
    now = now or (lambda: datetime.now(UTC))
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(state_dir, 0o700)
    lock_path = state_dir / ".capture.lock"
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("source recorder already running") from exc

        started = now()
        if not isinstance(started, datetime) or started.tzinfo is None:
            raise ValueError("VPS source recorder requires aware UTC clock")
        started = started.astimezone(UTC)
        date = started.date().isoformat()
        target = state_dir / date
        if target.exists() or target.is_symlink():
            raise ValueError("daily source receipt already exists, refusing overwrite")
        midnight = datetime.combine(started.date(), clock_time.min, tzinfo=UTC)
        deadline = midnight + timedelta(minutes=15)

        with tempfile.TemporaryDirectory(prefix=".funding-stage-", dir=state_dir) as stage:
            staging = Path(stage)
            evidence = staging / "source"
            evidence.mkdir(mode=0o700)
            outcome: dict[str, Any]
            files: tuple[str, ...]
            try:
                if not midnight <= started < deadline:
                    raise ValueError("VPS collector outside UTC 00:00..00:15 window")
                if not synced():
                    raise ValueError("VPS NTP clock is not confirmed synchronized")
                # No retry, replay or fallback source. capture_today independently
                # enforces both request/response boundaries and no lookahead.
                collector(evidence)
                present = {p.name for p in evidence.iterdir()}
                if present != set(SOURCE_FILES):
                    raise ValueError("VPS source capture must have exactly three files")
                files = SOURCE_FILES
                digest = _write_archive(staging / "original-source.zip", evidence, files)
                result = replay(
                    staging / "original-source.zip",
                    expected_zip_sha256=digest,
                    expected_entry_date=date,
                )
                # A local replay is internal consistency only. The digest
                # is locally issued and MUST NOT be treated as an independent
                # GitHub, time authority, or OKX signature.
                outcome = {
                    "status": "local_replay_only",
                    "entry_market_date": date,
                    "archive_sha256": digest,
                    "raw_file_sha256": result["raw_file_sha256"],
                    "canonical_source_sha256": result["canonical_source_sha256"],
                    "regime": result["regime"],
                }
            except Exception as exc:
                # Discard all partial raw source before preserving an error.
                for item in evidence.iterdir():
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                _persist_json(evidence / "error.json", {
                    "status": "UNASSESSED",
                    "reason": str(exc),
                    "error_type": type(exc).__name__,
                    "point_in_time_publication_verified": False,
                    "acquisition_approved": False,
                    "promotion_approved": False,
                })
                files = ("error.json",)
                archive = staging / "original-source.zip"
                if archive.exists():
                    archive.unlink()
                digest = _write_archive(archive, evidence, files)
                outcome = {
                    "status": "UNASSESSED",
                    "entry_market_date": None,
                    "reason": str(exc),
                    "archive_sha256": digest,
                }
            manifest: dict[str, Any] = {
                "schema_version": 1,
                "origin": "vps_systemd_local_only",
                "started_at": started.isoformat(),
                "intended_utc_day": date,
                **outcome,
                "files": list(files),
                "github_attestation_verified": False,
                "exchange_signed": False,
                "point_in_time_publication_verified": False,
                "acquisition_approved": False,
                "promotion_approved": False,
            }
            _persist_json(staging / "manifest.json", manifest)
            # No raw loose files should be retained outside the source ZIP.
            for item in evidence.iterdir():
                item.unlink()
            evidence.rmdir()
            # The state directory and its daily receipts are owner-private.
            # Even a failed attempt consumes the day: manual reruns cannot
            # rewrite a historical source state.
            os.rename(staging, target)
            fd = os.open(state_dir, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    args = parser.parse_args()
    report = collect_once(args.state_dir)
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    if report["status"] != "local_replay_only":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
