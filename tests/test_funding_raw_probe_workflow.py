from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/probe-funding-raw-regime-source.yml"
SCRIPT = ROOT / "scripts/probe_funding_raw_regime_source.py"


def test_raw_funding_probe_is_read_only_and_fixed_research_window() -> None:
    workflow = WORKFLOW.read_text()
    script = SCRIPT.read_text()
    assert "workflow_dispatch:" in workflow
    assert "2026-09-15" in workflow
    assert "2026-09-21" in workflow
    assert "acquire-historical-campaign" not in workflow
    assert "promote-" not in workflow
    assert "git push" not in workflow
    assert "funding-raw-regime-source-research" in workflow
    assert "plan_funding_regime_research" in script
    assert "raw-api-capture.json" in script
    assert "reconstructed-features.json" in script
    assert "acquisition_approved" in script
