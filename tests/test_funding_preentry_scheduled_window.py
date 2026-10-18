"""Deterministic scheduler timing/safety contract; zero live calls or sleeps."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/wait_for_funding_preentry_window.py"
SCHEDULED = ROOT / ".github/workflows/capture-funding-preentry-scheduled.yml"
MANUAL = ROOT / ".github/workflows/capture-funding-preentry-source.yml"
CAPTURE = ROOT / "scripts/capture_funding_preentry_source.py"


def _module():
    spec = importlib.util.spec_from_file_location("preentry_window_wait", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value)


@pytest.mark.parametrize(("started", "date"), [
    ("2026-10-18T23:37:00+00:00", "2026-10-19"),
    ("2026-10-18T23:59:59+00:00", "2026-10-19"),
    ("2026-10-19T00:00:00+00:00", "2026-10-19"),
    ("2026-10-19T00:14:59+00:00", "2026-10-19"),
    ("2026-10-19T07:37:00+08:00", "2026-10-19"),
])
def test_target_midnight_frozen_and_utc(started, date):
    result = _module().target_midnight(_time(started))
    assert result == _time(f"{date}T00:00:00+00:00")
    assert result.tzinfo == UTC


@pytest.mark.parametrize("started", [
    "2026-10-18T23:36:59+00:00",
    "2026-10-19T00:15:00+00:00",
    "2026-10-19T08:00:00+00:00",
    "2026-10-19T23:00:00+00:00",
])
def test_missed_or_unexpected_start_never_waits_to_next_midnight(started):
    with pytest.raises(ValueError, match="missed current UTC window"):
        _module().wait_for_preentry_window(
            now=lambda: _time(started), sleeper=lambda _: pytest.fail("must not sleep"),
        )


def test_utc_midnight_wait_bounded_and_no_prewindow_capture():
    clock = [_time("2026-10-18T23:59:57+00:00")]
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        clock[0] += timedelta(seconds=seconds)

    result = _module().wait_for_preentry_window(now=lambda: clock[0], sleeper=sleep)
    assert sleeps == [3.0]
    assert result["target_entry_date"] == "2026-10-19"
    assert result["runner_observed_at"] == "2026-10-19T00:00:00+00:00"
    assert result["point_in_time_publication_verified"] is False


@pytest.mark.parametrize("started", [
    "2026-10-19T00:00:00+00:00",
    "2026-10-19T00:14:59+00:00",
])
def test_late_queue_but_inside_window_can_attempt_immediately(started):
    result = _module().wait_for_preentry_window(
        now=lambda: _time(started), sleeper=lambda _: pytest.fail("no wait allowed"),
    )
    assert result["entry_at"] == "2026-10-19T00:15:00+00:00"


def test_paused_runner_missing_deadline_fails_closed():
    clock = [_time("2026-10-18T23:59:57+00:00")]

    def delayed_sleep(_):
        clock[0] = _time("2026-10-19T00:15:01+00:00")

    with pytest.raises(ValueError, match="00:15 deadline missed"):
        _module().wait_for_preentry_window(now=lambda: clock[0], sleeper=delayed_sleep)


def test_backwards_runner_clock_fails_closed():
    clock = [_time("2026-10-18T23:50:00+00:00")]

    def rollback(_):
        clock[0] -= timedelta(seconds=1)

    with pytest.raises(ValueError, match="moved backwards"):
        _module().wait_for_preentry_window(now=lambda: clock[0], sleeper=rollback)


def test_missing_timezone_and_stopped_clock_fail_closed():
    script = _module()
    with pytest.raises(ValueError, match="aware UTC clock"):
        script.target_midnight(datetime(2026, 10, 18, 23, 40))
    with pytest.raises(ValueError, match="maximum wait budget"):
        script.wait_for_preentry_window(
            now=lambda: _time("2026-10-18T23:45:00+00:00"), sleeper=lambda _: None,
        )


def test_failure_receipt_explicitly_unassessed(monkeypatch, tmp_path):
    script = _module()
    def fail():
        raise ValueError("missed UTC window")

    monkeypatch.setattr(script, "wait_for_preentry_window", fail)
    monkeypatch.setattr(sys, "argv", ["wait", "--output-dir", str(tmp_path)])
    with pytest.raises(ValueError, match="missed UTC window"):
        script.main()
    receipt = json.loads((tmp_path / "error.json").read_text())
    assert receipt["phase"] == "scheduled_preentry_wait"
    assert receipt["status"] == "UNASSESSED"
    assert receipt["point_in_time_publication_verified"] is False
    assert receipt["acquisition_approved"] is False
    assert receipt["promotion_approved"] is False


def test_schedule_workflow_reuses_original_fail_closed_capture_and_manual_is_untouched():
    wf = SCHEDULED.read_text()
    manual = MANUAL.read_text()
    wait = SCRIPT.read_text()
    capture = CAPTURE.read_text()
    assert "  schedule:" in wf and "cron: '37 23 * * *'" in wf
    assert "workflow_dispatch:" not in wf and "  push:" not in wf
    assert "if: github.run_attempt == 1" in wf
    assert "cancel-in-progress: false" in wf
    assert "timeout-minutes: 45" in wf
    assert all(term in wf for term in (
        "contents: read", "id-token: write", "attestations: write",
        "uv run python scripts/wait_for_funding_preentry_window.py",
        "uv run python scripts/capture_funding_preentry_source.py",
        "attest-build-provenance@v2", "if: always()", "retention-days: 90",
    ))
    assert wf.index("uv sync --all-extras --dev") < wf.index(
        "scripts/wait_for_funding_preentry_window.py"
    ) < wf.index("scripts/capture_funding_preentry_source.py")
    assert "  workflow_dispatch:" in manual
    assert "  schedule:" not in manual and "  push:" not in manual
    assert "client.get(" not in wait and "httpx" not in wait
    assert "client.get(" in capture and "client.post(" not in capture
    assert "preentry source capture must start at UTC 00:00..00:15" in capture
    assert "follow_redirects=False" in capture
