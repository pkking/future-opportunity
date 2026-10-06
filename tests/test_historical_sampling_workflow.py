from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/sample-historical-market-days.yml"


def test_sampling_workflow_is_read_only_and_does_not_touch_market_or_acquisition() -> None:
    text = WORKFLOW.read_text()

    assert "permissions:\n  contents: read\n" in text
    assert "actions: write" not in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "gh workflow run" not in text
    assert "git push" not in text
    assert "gh pr create" not in text
    assert "prepare_okx" not in text
    assert "Acquire Historical Campaign" not in text
    assert "tests/fixtures/historical" not in text


def test_sampling_workflow_selftest_uses_committed_golden_request() -> None:
    text = WORKFLOW.read_text()

    assert "funding-carry" in text
    assert "2026-01-01" in text
    assert "2026-01-31" in text
    assert "stage2-baseline-v1" in text
    assert "systematic-stratified-sha256-v1" in text
    assert "scripts/sample_historical_market_days.py" in text
    assert "historical-market-day-sample-" in text
