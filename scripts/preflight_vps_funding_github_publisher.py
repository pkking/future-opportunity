"""Read-only, secret-redacted VPS Funding GitHub publisher preflight.

Operator-invoked at any UTC time. Never invokes collector or publisher,
changes service configuration or credentials, or creates a GitHub release.
A read-only GitHub API GET DOES NOT prove Contents:write permission.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Callable

import httpx

from audit_github_vps_release import verify_release
from publish_vps_funding_github_release import API, REPO
from run_vps_funding_preentry import ntp_is_synchronized

# The running VPS uses these paths. Override only for offline tests.
TOKEN_FILE = Path("/etc/future-opportunity/github-token")
STATE_DIR = Path("/var/lib/future-opportunity-funding")
NTP_MARKER = Path("/run/systemd/timesync/synchronized")
PUBLISHER_SERVICE = Path(
    "/etc/systemd/system/future-opportunity-funding-github-publish.service"
)
COLLECTOR_DROPIN = Path(
    "/etc/systemd/system/future-opportunity-funding-capture.service.d/"
    "10-github-publish.conf"
)
PASS = "PASS"
FAIL = "FAIL"
UNASSESSED = "UNASSESSED"


def _entry_day(raw: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw) is None:
        raise ValueError("expected source day YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("source day is not a calendar date") from exc
    if parsed.isoformat() != raw:
        raise ValueError("source day is not canonical")
    return raw


def _check_file(path: Path, *, owner_uid: int = 0) -> bytes:
    info = path.lstat()  # reject symlinks to avoid token indirection
    if not stat.S_ISREG(info.st_mode) or info.st_uid != owner_uid:
        raise ValueError("credential is not a root-owned ordinary file")
    if stat.S_IMODE(info.st_mode) != 0o600 or not 0 < info.st_size <= 8192:
        raise ValueError("credential is not nonempty owner-only mode 0600")
    data = path.read_bytes()
    if len(data) != info.st_size or len(data) > 8192:
        raise ValueError("credential changed during preflight")
    try:
        token = data.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("credential is not UTF-8") from exc
    if not token or token != token.strip() or any(c.isspace() for c in token):
        raise ValueError("credential has whitespace or surrounding newline")
    return data  # NEVER include or display this value in any receipt


def _state_safe(state: Path) -> bool:
    """Check metadata only; cannot establish DynamicUser runtime read rights."""
    try:
        info = state.lstat()
        if stat.S_ISLNK(info.st_mode):
            # systemd DynamicUser StateDirectory is commonly a protected
            # symlink into /var/lib/private; allow no other destinations.
            resolved = state.resolve(strict=True)
            private_root = Path("/var/lib/private")
            if not resolved.is_relative_to(private_root):
                return False
            info = resolved.stat()
        return (
            stat.S_ISDIR(info.st_mode)
            and stat.S_IMODE(info.st_mode) & 0o022 == 0
        )
    except (OSError, RuntimeError, ValueError):
        return False


def _installed_units_ok(unit: Path, dropin: Path) -> bool:
    try:
        conf = unit.read_text(encoding="utf-8")
        hook = dropin.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    required = (
        "[Service]", "Type=oneshot", "DynamicUser=yes", "Restart=no",
        "LoadCredential=github_token:/etc/future-opportunity/github-token",
        "ExecStart=/opt/future-opportunity/.venv/bin/python "
        "/opt/future-opportunity/scripts/publish_vps_funding_github_release.py",
        "ProtectSystem=strict",
    )
    return all(text in conf for text in required) and (
        "OnSuccess=future-opportunity-funding-github-publish.service" in hook
    )


def _result(status: str, summary: str) -> dict[str, str]:
    if status not in (PASS, FAIL, UNASSESSED):
        raise ValueError("unknown preflight status")
    return {"status": status, "summary": summary}


def check_preflight(
    *, now: Callable[[], datetime], client: httpx.Client,
    token_path: Path = TOKEN_FILE, state_dir: Path = STATE_DIR,
    ntp_marker: Path = NTP_MARKER, unit: Path = PUBLISHER_SERVICE,
    dropin: Path = COLLECTOR_DROPIN, source_day: str | None = None,
    owner_uid: int = 0,
    verify: Callable[..., dict[str, Any]] = verify_release,
) -> dict[str, Any]:
    instant = now()
    if not isinstance(instant, datetime) or instant.tzinfo is None:
        raise ValueError("preflight requires a timezone-aware clock")
    instant = instant.astimezone(UTC)
    synced = ntp_is_synchronized(marker=ntp_marker, now=lambda: instant)
    state_ok = _state_safe(state_dir)
    unit_ok = _installed_units_ok(unit, dropin)
    checks = {
        "ntp_recent": _result(
            PASS if synced else FAIL,
            "recent local timesync marker (not independent UTC attestation)"
            if synced else "recent local timesync marker missing or stale",
        ),
        "local_state_metadata": _result(
            PASS if state_ok else FAIL,
            "private local state directory metadata; runtime UID access not proven"
            if state_ok else "state directory absent or unsafe; runtime UID access not proven",
        ),
        "installed_systemd_units": _result(
            PASS if unit_ok else FAIL,
            "publisher and OnSuccess configuration files match expected contract"
            if unit_ok else "publisher service or OnSuccess configuration is missing or divergent",
        ),
    }
    token: str | None = None
    try:
        token = _check_file(token_path, owner_uid=owner_uid).decode("utf-8")
        checks["credential_file"] = _result(
            PASS, "owner-only root credential file; no token content recorded"
        )
    except (OSError, ValueError, UnicodeError):
        checks["credential_file"] = _result(
            FAIL, "credential absent, invalid owner/mode, symlink or malformed"
        )

    if token is None:
        checks["github_authenticated_read"] = _result(
            UNASSESSED, "not attempted without valid local credential"
        )
    else:
        try:
            response = client.get(
                API,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            response.raise_for_status()
            repo = response.json()
            if not isinstance(repo, dict) or (
                repo.get("full_name") != REPO or repo.get("private") is not False
            ):
                checks["github_authenticated_read"] = _result(
                    FAIL, "read-only repository identity or visibility mismatch"
                )
            else:
                checks["github_authenticated_read"] = _result(
                    PASS, "authenticated read works; GitHub write scope unverified"
                )
        except (httpx.HTTPError, ValueError, TypeError):
            # No URL, token, response body, request headers or secrets in output.
            checks["github_authenticated_read"] = _result(
                UNASSESSED, "authenticated GitHub API read failed; scope unknown"
            )
        finally:
            token = None

    if source_day is None:
        checks["prior_immutable_source"] = _result(
            UNASSESSED, "optional prior-day immutable evidence review not requested"
        )
    else:
        day = _entry_day(source_day)
        if day > instant.date().isoformat() or (
            day == instant.date().isoformat()
            and instant.hour == 0 and instant.minute < 15
        ):
            checks["prior_immutable_source"] = _result(
                UNASSESSED, "source day's entry deadline has not completed"
            )
        else:
            try:
                review = verify(day, client=client)
                if review.get("status") != (
                    "github_immutable_release_metadata_and_offline_replay_only"
                ) or review.get("tag") != f"funding-vps-{day}":
                    checks["prior_immutable_source"] = _result(
                        FAIL, "prior-day original GitHub bytes not strictly verified"
                    )
                else:
                    checks["prior_immutable_source"] = _result(
                        PASS, "prior-day immutable GitHub original bytes replay verified; "
                        "GitHub release cryptographic attestation checked separately"
                    )
            except (httpx.HTTPError, ValueError, OSError, TypeError, KeyError):
                checks["prior_immutable_source"] = _result(
                    UNASSESSED, "prior-day GitHub Release or source review unavailable"
                )
    required = (
        "ntp_recent", "local_state_metadata", "installed_systemd_units",
        "credential_file", "github_authenticated_read",
    )
    ok = all(checks[name]["status"] == PASS for name in required)
    # If an explicit source day was requested, it is a required check.
    if source_day is not None:
        ok = ok and checks["prior_immutable_source"]["status"] == PASS
    return {
        "status": "PREFLIGHT_READ_ONLY_PASS" if ok else "UNASSESSED",
        "checked_at": instant.isoformat(),
        "repo": REPO,
        "checks": checks,
        "github_contents_write_permission_verified": False,
        "github_release_immutability_setting_verified": False,
        "publisher_dynamic_user_runtime_verified": False,
        "new_github_release_created": False,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-day",
        help="optional earlier UTC YYYY-MM-DD published Release to replay (read-only)",
    )
    parser.add_argument("--report-out", type=Path, help="new private report; never overwrite")
    args = parser.parse_args()
    with httpx.Client(timeout=httpx.Timeout(12.0)) as client:
        result = check_preflight(
            now=lambda: datetime.now(UTC), client=client,
            source_day=args.source_day,
        )
    if args.report_out is not None:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(args.report_out, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(result, out, indent=2, sort_keys=True)
            out.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PREFLIGHT_READ_ONLY_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
