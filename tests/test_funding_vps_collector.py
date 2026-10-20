"""Fully offline VPS systemd collector time, replay and durability checks."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from future_opportunity.backtest.funding_asof_capture import validate_preentry_source
from test_funding_asof_capture import _base

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/run_vps_funding_preentry.py"
SERVICE = ROOT / "deploy/systemd/future-opportunity-funding-capture.service"
TIMER = ROOT / "deploy/systemd/future-opportunity-funding-capture.timer"
CLOCK = datetime(2026, 9, 15, 0, 10, 0, tzinfo=UTC)


def _mod(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("funding_vps_capture", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_capture(output):
    raw, timing = _base()
    result = validate_preentry_source(raw, timing)
    for name, payload in (
        ("raw-api-capture.json", raw),
        ("http-timing.json", timing),
        ("preentry-research-evidence.json", result),
    ):
        (output / name).write_text(json.dumps(payload, sort_keys=True) + "\n")
    return result


def _archive_and_manifest(state):
    day = state / "2026-09-15"
    manifest = json.loads((day / "manifest.json").read_text())
    artifact = day / "original-source.zip"
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == manifest["archive_sha256"]
    with zipfile.ZipFile(artifact) as z:
        files = {name: json.loads(z.read(name)) for name in z.namelist()}
    return manifest, files


def test_vps_once_stores_replay_verified_source_without_signing(monkeypatch, tmp_path):
    mod = _mod(monkeypatch)
    state = tmp_path / "state"
    result = mod.collect_once(
        state, now=lambda: CLOCK, synced=lambda: True, collector=_make_capture,
    )
    manifest, members = _archive_and_manifest(state)
    assert manifest == result
    assert result["status"] == "local_replay_only"
    assert result["entry_market_date"] == "2026-09-15"
    assert result["origin"] == "vps_systemd_local_only"
    assert result["files"] == list(mod.SOURCE_FILES)
    assert set(members) == set(mod.SOURCE_FILES)
    assert result["github_attestation_verified"] is False
    assert result["point_in_time_publication_verified"] is False
    assert result["exchange_signed"] is False
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False
    assert len(result["archive_sha256"]) == 64
    assert not (state / "2026-09-15" / "source").exists()


def test_vps_prevents_second_attempt_or_overwrite(monkeypatch, tmp_path):
    mod = _mod(monkeypatch)
    state = tmp_path / "state"
    mod.collect_once(state, now=lambda: CLOCK, synced=lambda: True, collector=_make_capture)
    original = (state / "2026-09-15" / "original-source.zip").read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        mod.collect_once(
            state, now=lambda: CLOCK, synced=lambda: True,
            collector=lambda *_: pytest.fail("no second source GET"),
        )
    assert original == (state / "2026-09-15" / "original-source.zip").read_bytes()


@pytest.mark.parametrize("time", [
    datetime(2026, 9, 14, 23, 59, 59, tzinfo=UTC),
    datetime(2026, 9, 15, 0, 15, 0, tzinfo=UTC),
    datetime(2026, 9, 15, 1, 37, 54, tzinfo=UTC),
])
def test_vps_time_guard_rejects_before_network(monkeypatch, tmp_path, time):
    mod = _mod(monkeypatch)
    result = mod.collect_once(
        tmp_path / "state", now=lambda: time, synced=lambda: True,
        collector=lambda *_: pytest.fail("no source call outside UTC window"),
    )
    assert result["status"] == "UNASSESSED"
    assert result["entry_market_date"] is None
    assert result["github_attestation_verified"] is False
    day = time.date().isoformat()
    with zipfile.ZipFile(tmp_path / "state" / day / "original-source.zip") as z:
        assert z.namelist() == ["error.json"]
        receipt = json.loads(z.read("error.json"))
    assert receipt["status"] == "UNASSESSED"
    assert receipt["point_in_time_publication_verified"] is False


def test_vps_unsynced_clock_fails_closed(monkeypatch, tmp_path):
    mod = _mod(monkeypatch)
    state = tmp_path / "state"
    result = mod.collect_once(
        state, now=lambda: CLOCK, synced=lambda: False,
        collector=lambda *_: pytest.fail("no source call with unsynced clock"),
    )
    assert result["status"] == "UNASSESSED"
    assert "NTP" in result["reason"]
    with zipfile.ZipFile(state / "2026-09-15" / "original-source.zip") as z:
        assert z.namelist() == ["error.json"]


def test_vps_half_capture_or_corrupted_evidence_never_publishes(monkeypatch, tmp_path):
    mod = _mod(monkeypatch)
    def incomplete(out):
        (out / "raw-api-capture.json").write_text("{}")
        (out / "partial").write_text("forbidden")
        raise ValueError("source timeout")
    result = mod.collect_once(
        tmp_path / "state", now=lambda: CLOCK,
        synced=lambda: True, collector=incomplete,
    )
    assert result["status"] == "UNASSESSED"
    with zipfile.ZipFile(tmp_path / "state" / "2026-09-15" / "original-source.zip") as z:
        assert z.namelist() == ["error.json"]
    assert not (tmp_path / "state" / "2026-09-15" / "partial").exists()


def test_vps_replay_failure_fails_closed(monkeypatch, tmp_path):
    mod = _mod(monkeypatch)
    result = mod.collect_once(
        tmp_path / "state", now=lambda: CLOCK,
        synced=lambda: True, collector=_make_capture,
        replay=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("original ZIP replay corrupted")
        ),
    )
    assert result["status"] == "UNASSESSED"
    with zipfile.ZipFile(tmp_path / "state" / "2026-09-15" / "original-source.zip") as z:
        assert z.namelist() == ["error.json"]


def _marker(tmp_path, timestamp):
    path = tmp_path / "synchronized"
    path.touch()
    os.utime(path, (timestamp, timestamp))
    return path


def test_vps_timesync_marker_requires_recent_success_without_dbus(monkeypatch, tmp_path):
    mod = _mod(monkeypatch)
    fresh = _marker(tmp_path, CLOCK.timestamp() - 2048)
    assert mod.ntp_is_synchronized(marker=fresh, now=lambda: CLOCK) is True
    os.utime(fresh, (CLOCK.timestamp() - 7200, CLOCK.timestamp() - 7200))
    assert mod.ntp_is_synchronized(marker=fresh, now=lambda: CLOCK) is True
    os.utime(fresh, (CLOCK.timestamp() - 7200.01, CLOCK.timestamp() - 7200.01))
    assert mod.ntp_is_synchronized(marker=fresh, now=lambda: CLOCK) is False
    os.utime(fresh, (CLOCK.timestamp() + 1, CLOCK.timestamp() + 1))
    assert mod.ntp_is_synchronized(marker=fresh, now=lambda: CLOCK) is False
    assert mod.MAX_NTP_SYNC_AGE_SECONDS == 7200


def test_vps_timesync_marker_missing_symlink_directory_and_permission_fail_closed(
    monkeypatch, tmp_path,
):
    mod = _mod(monkeypatch)
    missing = tmp_path / "not-created"
    assert mod.ntp_is_synchronized(marker=missing, now=lambda: CLOCK) is False
    real = _marker(tmp_path, CLOCK.timestamp())
    link = tmp_path / "synced-link"
    link.symlink_to(real)
    assert mod.ntp_is_synchronized(marker=link, now=lambda: CLOCK) is False
    assert mod.ntp_is_synchronized(marker=tmp_path, now=lambda: CLOCK) is False
    assert mod.ntp_is_synchronized(
        marker=real, now=lambda: datetime(2026, 9, 15, 0, 10)
    ) is False

    class NotReadable:
        def lstat(self):
            raise PermissionError("sandbox path denied")

    assert mod.ntp_is_synchronized(marker=NotReadable(), now=lambda: CLOCK) is False


def test_stale_ntp_marker_prevents_source_get_and_writes_unassessed(monkeypatch, tmp_path):
    mod = _mod(monkeypatch)
    old = _marker(tmp_path, CLOCK.timestamp() - 9000)
    state = tmp_path / "state"
    result = mod.collect_once(
        state, now=lambda: CLOCK,
        synced=lambda: mod.ntp_is_synchronized(marker=old, now=lambda: CLOCK),
        collector=lambda *_: pytest.fail("must not call OKX after stale sync"),
    )
    assert result["status"] == "UNASSESSED"
    assert result["entry_market_date"] is None
    with zipfile.ZipFile(state / "2026-09-15" / "original-source.zip") as z:
        assert z.namelist() == ["error.json"]
        assert json.loads(z.read("error.json"))["status"] == "UNASSESSED"

def test_vps_service_and_timer_do_not_introduce_secrets_or_retry():
    service = SERVICE.read_text()
    timer = TIMER.read_text()
    script = SCRIPT.read_text()
    assert "OnCalendar=*-*-* 00:00:10 UTC" in timer
    assert "AccuracySec=1s" in timer
    assert "RandomizedDelaySec=0" in timer
    assert "Persistent=false" in timer
    assert "DynamicUser=yes" in service
    assert "StateDirectory=future-opportunity-funding" in service
    assert "StateDirectoryMode=0700" in service
    assert "ProtectSystem=strict" in service
    assert "NoNewPrivileges=yes" in service
    assert "Restart=no" in service
    assert "UMask=0077" in service
    assert "TimeoutStartSec=120s" in service
    assert "OnCalendar" not in service and "Persistent=true" not in timer
    assert "github.token" not in script
    assert "client.post(" not in script
    assert "capture_today" in script and "audit_zip" in script
    assert "point_in_time_publication_verified" in script


def test_non_aware_clock_fails_without_creating_observation(monkeypatch, tmp_path):
    mod = _mod(monkeypatch)
    with pytest.raises(ValueError, match="aware UTC clock"):
        mod.collect_once(
            tmp_path / "state",
            now=lambda: datetime(2026, 9, 15, 0, 10),
            synced=lambda: True,
            collector=lambda *_: pytest.fail("must not call source"),
        )
    assert not list((tmp_path / "state").glob("20*"))


def test_no_live_network_or_external_delivery_from_vps_module():
    source = SCRIPT.read_text()
    assert "httpx" not in source and "requests." not in source
    assert "subprocess.run(" not in source  # no D-Bus process in the sandbox
    assert "/run/systemd/timesync/synchronized" in source
    assert "MAX_NTP_SYNC_AGE_SECONDS" in source
    assert "github.com" not in source
