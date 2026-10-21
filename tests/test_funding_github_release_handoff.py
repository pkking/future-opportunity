"""No-network contract tests for prospective GitHub-only immutable source releases."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from test_funding_vps_receipt_audit import DAY, _files

ROOT = Path(__file__).parents[1]
PUBLISH = ROOT / "scripts/publish_vps_funding_github_release.py"
AUDIT = ROOT / "scripts/audit_github_vps_release.py"
SERVICE = ROOT / "deploy/systemd/future-opportunity-funding-github-publish.service"
DROPIN = ROOT / "deploy/systemd/future-opportunity-funding-capture.service.d/10-github-publish.conf"
CLOCK = datetime(2026, 9, 15, 0, 4, 0, tzinfo=UTC)
START = "2026-09-15T00:00:11Z"
RECEIVED = "2026-09-15T00:04:01Z"
PUBLISHED = "2026-09-15T00:04:02Z"
TAG = f"funding-vps-{DAY}"


def _modules(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    def load(name, file):
        spec = importlib.util.spec_from_file_location(name, file)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return load("funding_github_publisher", PUBLISH), load("funding_github_reviewer", AUDIT)


class MockGitHubRelease:
    def __init__(self):
        self.payload = {}
        self.assets = {}
        self.created_at = RECEIVED
        self.published_at = PUBLISHED
        self.immutable = True
        self.upload_wrong_digest = False
        self.fail_create = False
        self.calls = []

    def asset(self, name):
        value = self.assets[name]
        digest = hashlib.sha256(value).hexdigest()
        return {
            "id": (1 if name == "original-source.zip" else 2),
            "name": name,
            "size": len(value),
            "state": "uploaded",
            "digest": f"sha256:{'0'*64 if self.upload_wrong_digest else digest}",
            "created_at": self.created_at,
            "browser_download_url": (
                f"https://github.com/pkking/future-opportunity/releases/download/"
                f"{TAG}/{name}"
            ),
        }

    def release(self, draft=False):
        return {
            "id": 1234, "tag_name": TAG, "draft": draft,
            "immutable": self.immutable,
            "published_at": None if draft else self.published_at,
            "assets": [self.asset(name) for name in sorted(self.assets)],
        }

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append((request.method, str(request.url)))
        path = request.url.path
        if request.method == "POST" and path.endswith("/releases"):
            if self.fail_create:
                return httpx.Response(422, json={"message": "tag already exists"})
            self.payload = json.loads(request.content)
            return httpx.Response(201, json=self.release(draft=True))
        if request.method == "POST" and path.endswith("/1234/assets"):
            name = request.url.params.get("name")
            if name in self.assets:
                return httpx.Response(422, json={"message": "duplicate asset"})
            self.assets[name] = request.content
            return httpx.Response(201, json=self.asset(name))
        if request.method == "PATCH" and path.endswith("/releases/1234"):
            return httpx.Response(200, json=self.release(draft=False))
        if request.method == "GET" and path.endswith(f"/releases/tags/{TAG}"):
            return httpx.Response(200, json=self.release(draft=False))
        if request.method == "GET" and path.startswith(
            "/pkking/future-opportunity/releases/download/"
        ):
            return httpx.Response(200, content=self.assets[path.rsplit("/", 1)[1]])
        return httpx.Response(404, json={"message": "unexpected endpoint"})


def _setup(tmp_path):
    state = tmp_path / "state" / DAY
    state.mkdir(parents=True)
    _files(state)
    github = MockGitHubRelease()
    return state, github


def _publish(module, state, github, *, when=CLOCK, token="secret-test-only"):
    with httpx.Client(transport=httpx.MockTransport(github.handle)) as client:
        return module.publish_today(state.parent, client=client, token=token,
                                    now=lambda: when)


def _review(module, github):
    with httpx.Client(transport=httpx.MockTransport(github.handle)) as client:
        return module.verify_release(DAY, client=client)


def test_publish_two_original_assets_then_immutable_release(monkeypatch, tmp_path):
    publisher, reviewer = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    result = _publish(publisher, state, gh)
    assert result["status"] == "github_immutable_release_preentry_metadata_only"
    assert result["release_id"] == 1234
    assert [a["name"] for a in result["assets"]] == list(publisher.SOURCE_ASSETS)
    assert gh.assets["original-source.zip"] == (state / "original-source.zip").read_bytes()
    assert gh.assets["manifest.json"] == (state / "manifest.json").read_bytes()
    assert gh.payload["draft"] is True
    assert gh.payload["prerelease"] is True
    assert result["point_in_time_publication_verified"] is False
    assert result["promotion_approved"] is False
    assert len(gh.calls) == 4
    independent = _review(reviewer, gh)
    assert independent["status"] == "github_immutable_release_metadata_and_offline_replay_only"
    assert independent["archive_sha256"] == hashlib.sha256(
        gh.assets["original-source.zip"]
    ).hexdigest()
    assert independent["github_release_attestation_verified"] is False
    assert independent["point_in_time_publication_verified"] is False


@pytest.mark.parametrize("when", [
    datetime(2026, 9, 14, 23, 59, 59, tzinfo=UTC),
    datetime(2026, 9, 15, 0, 15, 0, tzinfo=UTC),
    datetime(2026, 9, 16, 0, 1, 0, tzinfo=UTC),
])
def test_no_backfill_or_late_capture_transmits_nothing(monkeypatch, tmp_path, when):
    publisher, _ = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    with pytest.raises(ValueError, match="window|backfilled"):
        _publish(publisher, state, gh, when=when)
    assert gh.calls == []


def test_source_failure_or_wrong_local_digest_never_calls_github(monkeypatch, tmp_path):
    publisher, _ = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    manifest = json.loads((state / "manifest.json").read_text())
    manifest["status"] = "UNASSESSED"
    (state / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="failed or malformed"):
        _publish(publisher, state, gh)
    assert not gh.calls
    manifest["status"] = "local_replay_only"
    manifest["archive_sha256"] = "0" * 64
    (state / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="digests mismatch"):
        _publish(publisher, state, gh)
    assert not gh.calls


def test_missing_credential_no_release(monkeypatch, tmp_path):
    publisher, _ = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    with pytest.raises(ValueError, match="credential"):
        _publish(publisher, state, gh, token="")
    assert gh.calls == []


@pytest.mark.parametrize("override,reason", [
    ({"fail_create": True}, "422"),
    ({"upload_wrong_digest": True}, "identity/digest"),
    ({"immutable": False}, "not immutable"),
    ({"published_at": "2026-09-15T00:15:00Z"}, "not immutable"),
    ({"created_at": "2026-09-15T00:15:00Z"}, "outside pre-entry"),
])
def test_github_api_inconsistency_fails_closed(monkeypatch, tmp_path, override, reason):
    publisher, _ = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    for name, value in override.items():
        setattr(gh, name, value)
    with pytest.raises((ValueError, httpx.HTTPStatusError), match=reason):
        _publish(publisher, state, gh)


@pytest.mark.parametrize("change,reason", [
    ({"immutable": False}, "immutable"),
    ({"published_at": "2026-09-15T00:15:00Z"}, "too late"),
    ({"created_at": "2026-09-15T00:16:00Z"}, "outside pre-entry"),
])
def test_public_reviewer_refuses_invalid_immutability_or_time(monkeypatch, tmp_path,
                                                                change, reason):
    publisher, reviewer = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    _publish(publisher, state, gh)
    for name, value in change.items():
        setattr(gh, name, value)
    with pytest.raises(ValueError, match=reason):
        _review(reviewer, gh)


def test_public_reviewer_refuses_replaced_asset_even_if_api_digest_follows(
    monkeypatch, tmp_path,
):
    publisher, reviewer = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    _publish(publisher, state, gh)
    gh.assets["original-source.zip"] += b"changed"
    with pytest.raises(ValueError, match="digest mismatch"):
        _review(reviewer, gh)


def test_source_collector_does_not_gain_credentials_or_http_upload():
    source = (ROOT / "scripts/run_vps_funding_preentry.py").read_text()
    original_service = (
        ROOT / "deploy/systemd/future-opportunity-funding-capture.service"
    ).read_text()
    optin = DROPIN.read_text()
    service = SERVICE.read_text()
    script = PUBLISH.read_text()
    assert "OnSuccess" not in original_service
    assert "LoadCredential" not in original_service
    assert "LoadCredential=github_token:" in service
    assert "DynamicUser=yes" in service
    assert "ProtectSystem=strict" in service
    assert "Restart=no" in service
    assert "OnSuccess=future-opportunity-funding-github-publish.service" in optin
    assert "Install" not in service
    assert "capture_today" not in script
    assert "capture_today" in source
    assert "client.post(" in script
    assert "httpx.Client" not in source
