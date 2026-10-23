"""Fault-injection contracts for existing prospective immutable Release publisher.

No real GitHub writes or OKX network. A partial draft never substitutes for
successful immutable publication or changes the already captured original ZIP.
"""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from test_funding_github_release_handoff import (
    _modules, _setup, CLOCK,
)

CANARY = "github_pat_TEST_ONLY_NEVER_REAL"
LATE = datetime(2026, 9, 15, 0, 15, 0, tzinfo=UTC)


def _attempt(monkeypatch, tmp_path, *, phase, failure, clock=None):
    publisher, _ = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    before = {
        name: (state / name).read_bytes()
        for name in ("manifest.json", "original-source.zip")
    }
    calls = []
    orig = gh.handle

    def handler(request):
        path = request.url.path
        calls.append((request.method, path, request.url.params.get("name")))
        # Forbidden POST/PATCH endpoint families other than draft/asset/publish.
        assert request.method in ("POST", "PATCH")
        if phase == "create" and path.endswith("/releases") and request.method == "POST":
            if failure == "timeout":
                raise httpx.ReadTimeout("mock timed out", request=request)
            return httpx.Response(503, json={"message": "mock unavailable"})
        if phase == "asset1" and request.url.params.get("name") == "original-source.zip":
            if failure == "timeout":
                raise httpx.ConnectError("mock connect lost", request=request)
            return httpx.Response(502, json={"message": "mock bad gateway"})
        if phase == "asset2" and request.url.params.get("name") == "manifest.json":
            if failure == "timeout":
                raise httpx.ReadTimeout("mock timed out", request=request)
            return httpx.Response(500, json={"message": "mock server failure"})
        if phase == "publish" and request.method == "PATCH":
            if failure == "timeout":
                raise httpx.ReadTimeout("mock publish timed out", request=request)
            return httpx.Response(503, json={"message": "mock unavailable"})
        return orig(request)

    if clock is None:
        now = lambda: CLOCK
    else:
        times = iter(clock)
        now = lambda: next(times)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises((httpx.RequestError, httpx.HTTPStatusError, ValueError)) as exc:
            publisher.publish_today(state.parent, token=CANARY, client=client, now=now)

    assert CANARY not in str(exc.value)
    assert CANARY not in repr(exc.value)
    assert all((state / name).read_bytes() == data for name, data in before.items())
    assert hashlib.sha256((state / "original-source.zip").read_bytes()).hexdigest() == (
        hashlib.sha256(before["original-source.zip"]).hexdigest()
    )
    # No upload may be retried and no existing source may be rewritten.
    assert len(calls) == len(set(calls))
    return gh, calls


@pytest.mark.parametrize("phase,failure", [
    ("create", "http"), ("create", "timeout"),
    ("asset1", "http"), ("asset1", "timeout"),
    ("asset2", "http"), ("asset2", "timeout"),
    ("publish", "http"), ("publish", "timeout"),
])
def test_any_github_network_phase_fails_closed_and_keeps_vps_originals(
    monkeypatch, tmp_path, phase, failure,
):
    gh, calls = _attempt(
        monkeypatch, tmp_path, phase=phase, failure=failure,
    )
    phases = [method for method, _, _ in calls]
    assert phases[0] == "POST"
    # Publish is impossible until GitHub accepted both original assets.
    if phase in ("create", "asset1", "asset2"):
        assert "PATCH" not in phases
    if phase == "create":
        assert not gh.assets
    if phase == "asset1":
        assert not gh.assets
    if phase == "asset2":
        assert set(gh.assets) == {"original-source.zip"}
    if phase == "publish":
        assert set(gh.assets) == {"original-source.zip", "manifest.json"}
        assert phases[-1] == "PATCH"


@pytest.mark.parametrize("guard_index,expected_uploads", [
    (3, ["original-source.zip"]),
    (4, ["original-source.zip", "manifest.json"]),
])
def test_utc_deadline_crossed_between_upload_phases_blocks_publish(
    monkeypatch, tmp_path, guard_index, expected_uploads,
):
    ticks = [CLOCK] * 5
    ticks[guard_index] = LATE
    # The correct boundary becomes late precisely at the named checkpoint.
    gh, calls = _attempt(
        monkeypatch, tmp_path, phase="none", failure="none", clock=ticks,
    )
    assert list(gh.assets) == expected_uploads
    assert "PATCH" not in [m for m, _, _ in calls]


def test_missing_source_zip_refuses_any_github_request(monkeypatch, tmp_path):
    publisher, _ = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    (state / "original-source.zip").unlink()
    with httpx.Client(transport=httpx.MockTransport(gh.handle)) as client:
        with pytest.raises((OSError, ValueError)):
            publisher.publish_today(
                state.parent, token=CANARY, client=client, now=lambda: CLOCK,
            )
    assert not gh.calls


def test_git_api_never_writes_token_to_original_archive(monkeypatch, tmp_path):
    publisher, _ = _modules(monkeypatch)
    state, gh = _setup(tmp_path)
    original_zip = (state / "original-source.zip").read_bytes()
    original_manifest = (state / "manifest.json").read_bytes()
    with httpx.Client(transport=httpx.MockTransport(gh.handle)) as client:
        result = publisher.publish_today(
            state.parent, token=CANARY, client=client, now=lambda: CLOCK,
        )
    assert result["status"] == "github_immutable_release_preentry_metadata_only"
    assert CANARY not in repr(result)
    assert (state / "original-source.zip").read_bytes() == original_zip
    assert (state / "manifest.json").read_bytes() == original_manifest
    assert gh.assets["original-source.zip"] == original_zip
    assert gh.assets["manifest.json"] == original_manifest
    assert all(
        method in ("POST", "PATCH")
        for method, _ in gh.calls
    )
