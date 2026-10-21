"""GitHub-only, strictly prospective immutable Release publisher for VPS Funding evidence.

This is an optional POST-capture handoff, never an OKX market-source fetch.
Publish each original local ZIP+manifest as GitHub assets before UTC 00:15,
then require GitHub's own published metadata to indicate immutable Release.
No backfill, no endpoint override, no secrets in logs or on disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable

import httpx

from audit_vps_funding_capture import audit_vps_receipt

REPO = "pkking/future-opportunity"
API = f"https://api.github.com/repos/{REPO}"
UPLOAD = f"https://uploads.github.com/repos/{REPO}"
SOURCE_ASSETS = ("original-source.zip", "manifest.json")
MAX_ZIP_BYTES = 5_000_000
MAX_MANIFEST_BYTES = 65_536


def _clock_now() -> datetime:
    return datetime.now(UTC)


def _date_guard(today: str, now: Callable[[], datetime]) -> datetime:
    clock = now()
    if not isinstance(clock, datetime) or clock.tzinfo is None:
        raise ValueError("publisher requires aware UTC clock")
    current = clock.astimezone(UTC)
    midnight = datetime.combine(current.date(), time.min, tzinfo=UTC)
    if not midnight <= current < midnight + timedelta(minutes=15):
        raise ValueError("GitHub handoff outside UTC 00:00..00:15 window")
    if today != current.date().isoformat():
        raise ValueError("GitHub evidence cannot be backfilled or forwarded to another day")
    return current


def _api_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"GitHub {field} missing")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"GitHub {field} is invalid") from exc
    if result.tzinfo is None:
        raise ValueError(f"GitHub {field} must have timezone")
    return result.astimezone(UTC)


def _bounded_original(path: Path, max_bytes: int) -> bytes:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= max_bytes:
        raise ValueError("GitHub publisher needs a bounded original regular file")
    original = path.read_bytes()
    if len(original) != info.st_size:
        raise ValueError("original changed while reading")
    return original


def _github_json(client: httpx.Client, method: str, path: str, *,
                 token: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.request(
        method, API + path,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json=payload,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("GitHub API response must be JSON object")
    return data


def _github_asset(client: httpx.Client, release_id: int, name: str,
                  content: bytes, token: str) -> dict[str, Any]:
    response = client.post(
        f"{UPLOAD}/releases/{release_id}/assets",
        params={"name": name},
        content=content,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                 "Accept": "application/vnd.github+json"},
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("GitHub asset response must be JSON object")
    return data


def _confirm_asset(name: str, data: dict[str, Any], expected: bytes,
                   day: str) -> dict[str, str | int]:
    actual_sha = hashlib.sha256(expected).hexdigest()
    if (
        data.get("name") != name
        or data.get("state") != "uploaded"
        or type(data.get("size")) is not int
        or data["size"] != len(expected)
        or data.get("digest") != f"sha256:{actual_sha}"
        or type(data.get("id")) is not int
    ):
        raise ValueError("GitHub asset identity/digest/size mismatch")
    created = _api_time(data.get("created_at"), "asset created_at")
    midnight = datetime.combine(datetime.fromisoformat(day).date(), time.min, tzinfo=UTC)
    if not midnight <= created < midnight + timedelta(minutes=15):
        raise ValueError("GitHub server asset created_at outside pre-entry window")
    return {"name": name, "id": data["id"], "digest": actual_sha,
            "created_at": created.isoformat()}


def publish_today(
    state_dir: Path, *, token: str,
    now: Callable[[], datetime] = _clock_now,
    client: httpx.Client,
) -> dict[str, Any]:
    """Create one new GitHub Release; fail closed without deleting/replacing it."""
    current = now()
    if not isinstance(current, datetime) or current.tzinfo is None:
        raise ValueError("publisher requires aware UTC clock")
    day = _date_guard(current.astimezone(UTC).date().isoformat(), lambda: current)
    date_str = day.date().isoformat()
    receipt_dir = state_dir / date_str
    if not receipt_dir.is_dir() or receipt_dir.is_symlink():
        raise ValueError("no current UTC-day local receipt; cannot backfill")
    originals = {
        name: _bounded_original(receipt_dir / name, MAX_ZIP_BYTES if name.endswith(".zip")
                                else MAX_MANIFEST_BYTES)
        for name in SOURCE_ASSETS
    }
    manifest = json.loads(originals["manifest.json"])
    if not isinstance(manifest, dict) or manifest.get("status") != "local_replay_only":
        raise ValueError("cannot publish failed or malformed local VPS observation")
    local_digest = hashlib.sha256(originals["original-source.zip"]).hexdigest()
    if local_digest != manifest.get("archive_sha256"):
        raise ValueError("local ZIP and local manifest digests mismatch")
    # Verify original bytes and their strict no-lookahead constraints locally.
    local_check = audit_vps_receipt(
        receipt_dir / "manifest.json", receipt_dir / "original-source.zip",
        expected_zip_sha256=local_digest, expected_entry_date=date_str,
    )
    if local_check["status"] != "offline_vps_replay_only":
        raise ValueError("local source did not pass strict replay")
    if not isinstance(token, str) or not token.strip() or "\n" in token or "\r" in token:
        raise ValueError("GitHub Contents:write credential is required")
    _date_guard(date_str, now)
    tag = f"funding-vps-{date_str}"
    release = _github_json(client, "POST", "/releases", token=token, payload={
        "tag_name": tag, "target_commitish": "main",
        "name": f"Funding VPS original evidence {date_str}",
        "body": f"Research only; VPS local source SHA256: {local_digest}; not exchange-signed.",
        "draft": True, "prerelease": True, "make_latest": "false",
    })
    release_id = release.get("id")
    if type(release_id) is not int or release.get("tag_name") != tag or release.get("draft") is not True:
        raise ValueError("GitHub draft response identity mismatch")
    confirmed = []
    for name in SOURCE_ASSETS:
        _date_guard(date_str, now)
        asset = _github_asset(client, release_id, name, originals[name], token)
        confirmed.append(_confirm_asset(name, asset, originals[name], date_str))
    _date_guard(date_str, now)
    published = _github_json(
        client, "PATCH", f"/releases/{release_id}",
        token=token, payload={"draft": False, "prerelease": True, "make_latest": "false"},
    )
    published_at = _api_time(published.get("published_at"), "release published_at")
    midnight = datetime.combine(day.date(), time.min, tzinfo=UTC)
    if (
        published.get("id") != release_id
        or published.get("tag_name") != tag
        or published.get("draft") is not False
        or published.get("immutable") is not True
        or not midnight <= published_at < midnight + timedelta(minutes=15)
        or any(_api_time(asset["created_at"], "asset created_at") > published_at
               for asset in confirmed)
    ):
        raise ValueError("GitHub release not immutable or not published before entry")
    # GitHub created_at/published_at are GitHub server API metadata. Neither
    # alone authenticates OKX dissemination; future review must verify
    # release attestation and download exact original bytes independently.
    return {
        "status": "github_immutable_release_preentry_metadata_only",
        "origin": "vps_systemd_local_only",
        "entry_market_date": date_str,
        "repo": REPO,
        "tag": tag,
        "release_id": release_id,
        "published_at": published_at.isoformat(),
        "assets": confirmed,
        "github_release_attestation_verified": False,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    args = parser.parse_args()
    # Only systemd LoadCredential supplies this token to a separate service.
    cred_dir = os.environ.get("CREDENTIALS_DIRECTORY")
    if not cred_dir:
        raise SystemExit("GitHub credential directory not configured; no upload")
    token = (Path(cred_dir) / "github_token").read_text(encoding="utf-8").strip()
    with httpx.Client(timeout=httpx.Timeout(8.0), follow_redirects=False) as client:
        result = publish_today(args.state_dir, token=token, client=client)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
