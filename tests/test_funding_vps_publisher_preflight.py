"""No-network checks for read-only publisher preflight, with no secret leakage."""
from __future__ import annotations

import importlib.util
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/preflight_vps_funding_github_publisher.py"
NOW = datetime(2026, 10, 24, 18, 30, tzinfo=UTC)
TOKEN = "github_pat_FAKE_IN_TESTS_ONLY"


def _module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("vps_preflight_test", SCRIPT)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def _paths(tmp_path):
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    marker = tmp_path / "sync"
    marker.write_text("")
    os.utime(marker, (NOW.timestamp(), NOW.timestamp()))
    unit = tmp_path / "publish.service"
    unit.write_text(
        "[Service]\nType=oneshot\nDynamicUser=yes\nRestart=no\n"
        "LoadCredential=github_token:/etc/future-opportunity/github-token\n"
        "ExecStart=/opt/future-opportunity/.venv/bin/python "
        "/opt/future-opportunity/scripts/publish_vps_funding_github_release.py "
        "--state-dir /var/lib/future-opportunity-funding\n"
        "ProtectSystem=strict\n"
    )
    dropin = tmp_path / "10-github-publish.conf"
    dropin.write_text(
        "[Unit]\nOnSuccess=future-opportunity-funding-github-publish.service\n"
    )
    token = tmp_path / "github-token"
    token.write_text(TOKEN)
    token.chmod(0o600)
    return {
        "token_path": token, "ntp_marker": marker,
        "state_dir": state, "unit": unit, "dropin": dropin,
        "owner_uid": os.getuid(),
    }


def _client(*, status=200, identity=None, disconnect=False):
    calls = []
    def handler(request):
        calls.append((request.method, str(request.url), request.headers.get("Authorization")))
        assert request.method == "GET"  # forbidden GitHub writes
        if disconnect:
            raise httpx.ConnectError("offline", request=request)
        if request.url.path == "/repos/pkking/future-opportunity":
            return httpx.Response(
                status,
                json=identity or {"full_name": "pkking/future-opportunity", "private": False},
            )
        raise AssertionError("unexpected GitHub endpoint")
    return httpx.Client(transport=httpx.MockTransport(handler)), calls


def _run(monkeypatch, tmp_path, *, status=200, identity=None, disconnect=False,
         source_day=None, verify=None, mutate=None):
    m = _module(monkeypatch)
    paths = _paths(tmp_path)
    if mutate is not None:
        mutate(paths)
    client, calls = _client(status=status, identity=identity, disconnect=disconnect)
    kwargs = dict(now=lambda: NOW, client=client, source_day=source_day, **paths)
    if verify is not None:
        kwargs["verify"] = verify
    with client:
        report = m.check_preflight(**kwargs)
    assert TOKEN not in json.dumps(report)
    assert all(method == "GET" for method, _, _ in calls)
    return report, calls


def test_success_only_proves_local_hygiene_and_authenticated_read(monkeypatch, tmp_path):
    report, calls = _run(monkeypatch, tmp_path)
    assert report["status"] == "PREFLIGHT_READ_ONLY_PASS"
    assert len(calls) == 1 and calls[0][2] == "Bearer " + TOKEN
    assert all(report["checks"][name]["status"] == "PASS" for name in (
        "ntp_recent", "local_state_metadata", "installed_systemd_units",
        "credential_file", "github_authenticated_read",
    ))
    assert report["checks"]["prior_immutable_source"]["status"] == "UNASSESSED"
    assert report["github_contents_write_permission_verified"] is False
    assert report["github_release_immutability_setting_verified"] is False
    assert report["publisher_dynamic_user_runtime_verified"] is False
    assert report["new_github_release_created"] is False
    for name in ("exchange_signed", "point_in_time_publication_verified",
                 "acquisition_approved", "promotion_approved"):
        assert report[name] is False


@pytest.mark.parametrize("kind", [
    "missing", "symlink", "mode", "empty", "newline", "owner",
])
def test_invalid_token_files_fail_closed_without_rest_calls(monkeypatch, tmp_path, kind):
    def mutate(paths):
        token = paths["token_path"]
        if kind == "missing":
            token.unlink()
        elif kind == "symlink":
            real = token.with_name("actual")
            token.rename(real)
            token.symlink_to(real)
        elif kind == "mode":
            token.chmod(0o640)
        elif kind == "empty":
            token.write_text("")
        elif kind == "newline":
            token.write_text(TOKEN + "\n")
        elif kind == "owner":
            paths["owner_uid"] += 1
    report, calls = _run(monkeypatch, tmp_path, mutate=mutate)
    assert report["status"] == "UNASSESSED"
    assert report["checks"]["credential_file"]["status"] == "FAIL"
    assert report["checks"]["github_authenticated_read"]["status"] == "UNASSESSED"
    assert not calls


@pytest.mark.parametrize("kind", ["stale-ntp", "missing-ntp", "open-state", "missing-unit"])
def test_bad_runtime_prerequisites_fail_closed(monkeypatch, tmp_path, kind):
    def mutate(paths):
        if kind == "stale-ntp":
            t = NOW.timestamp() - 2 * 3600 - 1
            os.utime(paths["ntp_marker"], (t, t))
        elif kind == "missing-ntp":
            paths["ntp_marker"].unlink()
        elif kind == "open-state":
            paths["state_dir"].chmod(0o777)
        elif kind == "missing-unit":
            paths["unit"].unlink()
    report, _ = _run(monkeypatch, tmp_path, mutate=mutate)
    assert report["status"] == "UNASSESSED"
    assert any(v["status"] == "FAIL" for v in report["checks"].values())


@pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
def test_auth_network_errors_never_claim_write_scope(monkeypatch, tmp_path, status):
    report, _ = _run(monkeypatch, tmp_path, status=status)
    assert report["status"] == "UNASSESSED"
    assert report["checks"]["github_authenticated_read"]["status"] == "UNASSESSED"


def test_offline_and_wrong_repository_fail_closed(monkeypatch, tmp_path):
    report, _ = _run(monkeypatch, tmp_path, disconnect=True)
    assert report["status"] == "UNASSESSED"
    report, _ = _run(
        monkeypatch, tmp_path / "other",
        identity={"full_name": "somebody/other", "private": False},
    )
    assert report["checks"]["github_authenticated_read"]["status"] == "FAIL"


def test_past_existing_release_verifies_only_strict_source_replay(monkeypatch, tmp_path):
    def verified(day, *, client):
        assert day == "2026-10-23"
        return {
            "status": "github_immutable_release_metadata_and_offline_replay_only",
            "tag": "funding-vps-2026-10-23",
        }
    report, _ = _run(
        monkeypatch, tmp_path, source_day="2026-10-23", verify=verified,
    )
    assert report["status"] == "PREFLIGHT_READ_ONLY_PASS"
    assert report["checks"]["prior_immutable_source"]["status"] == "PASS"


def test_prior_release_missing_or_late_is_not_reported_as_healthy(monkeypatch, tmp_path):
    def rejected(day, *, client):
        raise ValueError("GitHub Release published after 00:15")
    report, _ = _run(
        monkeypatch, tmp_path, source_day="2026-10-23", verify=rejected,
    )
    assert report["status"] == "UNASSESSED"
    assert report["checks"]["prior_immutable_source"]["status"] == "UNASSESSED"


def test_source_day_future_and_invalid_inputs(monkeypatch, tmp_path):
    report, _ = _run(monkeypatch, tmp_path, source_day="2026-10-25")
    assert report["status"] == "UNASSESSED"
    for bad in ("2026-10-35", "2026-1-23", "tomorrow"):
        with pytest.raises(ValueError, match="source day"):
            p = tmp_path / bad.replace("/", "_")
            p.mkdir()
            _run(monkeypatch, p, source_day=bad)


def test_unaware_clock_rejected_and_no_write_functions_in_script(monkeypatch, tmp_path):
    m = _module(monkeypatch)
    with _client()[0] as client:
        with pytest.raises(ValueError, match="timezone"):
            m.check_preflight(now=lambda: datetime(2026, 10, 24), client=client)
    code = SCRIPT.read_text()
    assert "from audit_github_vps_release import verify_release" in code
    for banned in (
        "publish_today(", "capture_today(", "client.post(", "client.patch(",
        "client.put(", "client.delete(", "subprocess.", "systemctl start",
        "gh release create", "api.okx.com",
    ):
        assert banned not in code
