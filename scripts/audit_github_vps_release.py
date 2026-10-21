"""Independent public GitHub Release time+original-bytes review, research only.

Checks an already-published immutable GitHub Release and downloads the two
original VPS assets, then reuses the strict offline reviewer. Never authenticates
OKX as-of-publication, never promotes sources and never writes GitHub data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable

import httpx

from audit_vps_funding_capture import audit_vps_receipt
from publish_vps_funding_github_release import (
    API, REPO, SOURCE_ASSETS, MAX_MANIFEST_BYTES, MAX_ZIP_BYTES,
    _api_time, _confirm_asset,
)


def verify_release(
    entry_day: str, *, client: httpx.Client,
) -> dict[str, Any]:
    """Verify original bytes against GitHub public server metadata."""
    try:
        parsed_day = datetime.fromisoformat(entry_day).date()
    except (ValueError, TypeError) as exc:
        raise ValueError("expected UTC day must be YYYY-MM-DD") from exc
    if parsed_day.isoformat() != entry_day:
        raise ValueError("expected UTC day must be canonical")
    tag = f"funding-vps-{entry_day}"
    request = client.get(
        f"{API}/releases/tags/{tag}",
        headers={"Accept": "application/vnd.github+json"},
    )
    request.raise_for_status()
    release = request.json()
    if not isinstance(release, dict):
        raise ValueError("GitHub release metadata invalid")
    if (
        release.get("tag_name") != tag
        or release.get("draft") is not False
        or release.get("immutable") is not True
        or type(release.get("id")) is not int
    ):
        raise ValueError("GitHub Release must be published and immutable")
    midnight = datetime.combine(parsed_day, time.min, tzinfo=UTC)
    deadline = midnight + timedelta(minutes=15)
    published = _api_time(release.get("published_at"), "published_at")
    if not midnight <= published < deadline:
        raise ValueError("GitHub Release published too late for research entry")

    assets = release.get("assets")
    if not isinstance(assets, list) or len(assets) != 2:
        raise ValueError("exactly two GitHub original assets are required")
    by_name = {a.get("name"): a for a in assets if isinstance(a, dict)}
    if set(by_name) != set(SOURCE_ASSETS) or len(by_name) != len(assets):
        raise ValueError("GitHub original asset names must be unique and exact")
    fetched: dict[str, bytes] = {}
    metadata: list[dict[str, Any]] = []
    for name in SOURCE_ASSETS:
        obj = by_name[name]
        if (
            type(obj.get("id")) is not int
            or type(obj.get("size")) is not int
            or not 0 < obj["size"] <= (MAX_ZIP_BYTES if name.endswith(".zip")
                                      else MAX_MANIFEST_BYTES)
        ):
            raise ValueError("GitHub source asset missing valid id/size")
        expected_url = f"https://github.com/{REPO}/releases/download/{tag}/{name}"
        if obj.get("browser_download_url") != expected_url:
            raise ValueError("GitHub source asset URL identity mismatch")
        response = client.get(expected_url, follow_redirects=True)
        response.raise_for_status()
        if len(response.content) != obj["size"]:
            raise ValueError("GitHub downloaded asset size disagrees with metadata")
        details = _confirm_asset(name, obj, response.content, entry_day)
        if _api_time(details["created_at"], "asset created_at") > published:
            raise ValueError("GitHub asset created after Release published")
        fetched[name] = response.content
        metadata.append(details)

    with tempfile.TemporaryDirectory(prefix="funding-gh-release-review-") as tmp:
        root = Path(tmp)
        for name in SOURCE_ASSETS:
            (root / name).write_bytes(fetched[name])
        digest = hashlib.sha256(fetched["original-source.zip"]).hexdigest()
        replay = audit_vps_receipt(
            root / "manifest.json", root / "original-source.zip",
            expected_zip_sha256=digest,
            expected_entry_date=entry_day,
        )
    if replay["status"] != "offline_vps_replay_only":
        raise ValueError("GitHub Release evidence is not an original successful VPS capture")
    return {
        "status": "github_immutable_release_metadata_and_offline_replay_only",
        "repo": REPO,
        "tag": tag,
        "release_id": release["id"],
        "published_at": published.isoformat(),
        "assets": metadata,
        "entry_market_date": entry_day,
        "archive_sha256": digest,
        "regime": replay["regime"],
        "github_release_attestation_verified": False,
        "source_authentication_status": "requires_independent_provenance_review",
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "note": (
            "GitHub's server metadata and original bytes establish a "
            "GitHub-hosted pre-entry copy, not when OKX first published "
            "the underlying information. Independently run 'gh release "
            "verify TAG' and 'gh release verify-asset TAG PATH' to "
            "cryptographically verify release attestations."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry-date", required=True)
    args = parser.parse_args()
    with httpx.Client(timeout=httpx.Timeout(12.0)) as client:
        result = verify_release(args.entry_date, client=client)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
