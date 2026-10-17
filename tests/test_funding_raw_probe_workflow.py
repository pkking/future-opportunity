from __future__ import annotations

import json
from pathlib import Path
import importlib.util

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "probe_funding_raw_regime_source",
    ROOT / "scripts/probe_funding_raw_regime_source.py",
)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
WORKFLOW = ROOT / ".github/workflows/probe-funding-raw-regime-source.yml"
SCRIPT = ROOT / "scripts/probe_funding_raw_regime_source.py"
FROZEN = ROOT / "docs/historical-acquisition-plans/funding-2026-sep-oct-regime-source-windows-v1.json"


def test_raw_funding_probe_is_read_only_and_source_windows_precommitted() -> None:
    workflow = WORKFLOW.read_text()
    script = SCRIPT.read_text()
    raw = json.loads(FROZEN.read_text())
    assert raw["outcome_blind"] is True
    assert raw["selection_before_source_inspection"] is True
    assert raw["acquisition_approved"] is False
    assert raw["promotion_approved"] is False
    assert len(raw["candidate_windows"]) == 3
    for window in raw["candidate_windows"]:
        assert window["id"] in workflow
        assert probe.registered_research_window(window["id"]) == window
    assert "workflow_dispatch:" in workflow
    assert "contents: read" in workflow
    assert "fail-fast: false" in workflow
    assert "matrix.window_id" in workflow
    assert "acquire-historical-campaign" not in workflow
    assert "promote-" not in workflow
    assert "git push" not in workflow
    assert "funding-raw-regime-source-" in workflow
    assert "plan_funding_regime_research" in script
    assert "raw-api-capture.json" in script
    assert "reconstructed-features.json" in script
    assert "coverage-summary.json" in script
    assert "acquisition_approved" in script


def test_unregistered_and_corrupted_research_windows_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="unknown"):
        probe.registered_research_window("date-chosen-after-return")
    original = json.loads(FROZEN.read_text())
    scenarios = [
        ("duplicate or overlapping", lambda r: r["candidate_windows"][1].update(
            {"start_date": r["candidate_windows"][0]["start_date"],
             "end_date": r["candidate_windows"][0]["end_date"]})),
        ("governance", lambda r: r.update({"acquisition_approved": True})),
        ("seven historical days", lambda r: r["candidate_windows"][0].update(
            {"end_date": "2026-09-10"})),
    ]
    for idx, (message, change) in enumerate(scenarios):
        mutated = json.loads(json.dumps(original))
        change(mutated)
        target = tmp_path / f"invalid-{idx}.json"
        target.write_text(json.dumps(mutated))
        monkeypatch.setattr(probe, "WINDOWS_PATH", target)
        with pytest.raises(ValueError, match=message):
            probe.registered_research_window("2026-09-01-to-07")
