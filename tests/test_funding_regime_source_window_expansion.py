from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "probe_funding_expansion",
    ROOT / "scripts/probe_funding_raw_regime_source.py",
)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

OLD_REGISTRY = ROOT / "docs/historical-acquisition-plans/funding-2026-sep-oct-regime-source-windows-v1.json"
NEW_REGISTRY = ROOT / "docs/historical-acquisition-plans/funding-2026-jul-aug-regime-source-windows-v1.json"
OLD_WORKFLOW = ROOT / ".github/workflows/probe-funding-raw-regime-source.yml"
NEW_WORKFLOW = ROOT / ".github/workflows/probe-funding-jul-aug-regime-source.yml"


def test_two_independently_frozen_research_cohorts_are_outcome_blind() -> None:
    earlier = json.loads(OLD_REGISTRY.read_text())
    later = json.loads(NEW_REGISTRY.read_text())
    windows = earlier["candidate_windows"] + later["candidate_windows"]
    assert len(windows) == 6
    assert {w["id"] for w in windows} == set(probe.registered_research_window(w["id"])["id"] for w in windows)
    for w in windows:
        assert probe.registered_research_window(w["id"]) == w
    for registry in (earlier, later):
        assert registry["research_only"] is True
        assert registry["outcome_blind"] is True
        assert registry["selection_before_source_inspection"] is True
        assert registry["acquisition_approved"] is False
        assert registry["promotion_approved"] is False
        assert registry["volatility_threshold_bps"] == "100"
        assert registry["request_per_regime"] == 2
    assert max(w["end_date"] for w in later["candidate_windows"]) < min(
        w["start_date"] for w in earlier["candidate_windows"]
    )


def test_source_workflows_are_manual_read_only_and_bounded() -> None:
    before = OLD_WORKFLOW.read_text()
    after = NEW_WORKFLOW.read_text()
    for text in (before, after):
        assert "workflow_dispatch:" in text
        assert "push:" not in text
        assert "schedule:" not in text
        assert "contents: read" in text
        assert "fail-fast: false" in text
        assert "promote-historical-" not in text
        assert "acquire-historical-" not in text
        assert "git push" not in text
        assert "actions: write" not in text
    for w in json.loads(NEW_REGISTRY.read_text())["candidate_windows"]:
        assert w["id"] in after


@pytest.mark.parametrize("mutation,expected", [
    (lambda r: r["candidate_windows"][0].update({"seed": "returns-picked"}),
     "frozen windows"),
    (lambda r: r["candidate_windows"][0].update({"start_date": "2026-07-28"}),
     "seven historical days"),
    (lambda r: r.update({"promotion_approved": True}),
     "governance"),
    (lambda r: r.update({"outcome_blind": False}),
     "governance"),
])
def test_new_study_mutations_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutation,
    expected: str,
) -> None:
    obj = json.loads(NEW_REGISTRY.read_text())
    mutation(obj)
    path = tmp_path / "mutated.json"
    path.write_text(json.dumps(obj))
    monkeypatch.setattr(probe, "EXPANSION_WINDOWS_PATH", path)
    with pytest.raises(ValueError, match=expected):
        probe.registered_research_window("2026-07-27-to-08-02")
