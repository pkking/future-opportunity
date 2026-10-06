from pathlib import Path


ROOT = Path(__file__).parents[1]
ACQUIRE = ROOT / ".github/workflows/acquire-historical-campaign.yml"
PLANNER = ROOT / ".github/workflows/plan-historical-campaign.yml"


def test_acquisition_workflow_is_corpus_read_only() -> None:
    text = ACQUIRE.read_text()

    assert "permissions:\n  contents: read\n" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "git push" not in text
    assert "gh pr create" not in text
    assert "tests/fixtures/historical" not in text


def test_planner_workflow_remains_read_only_and_only_follows_successful_acquisition() -> None:
    text = PLANNER.read_text()

    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "workflows: [\"Acquire Historical Campaign\"]" in text
    assert "github.event.workflow_run.conclusion == 'success'" in text
    assert "historical-acquisition-control" in text
    assert "gh pr create" not in text
    assert "git push" not in text


def test_acquisition_workflow_propagates_funding_selection_provenance() -> None:
    text = ACQUIRE.read_text()

    assert "funding_selection_provenance:" in text
    assert "steps.resolve.outputs.funding_selection_provenance" in text
    assert "selection_provenance_json:" in text
    assert "needs.resolve.outputs.funding_selection_provenance" in text


def test_acquisition_workflow_propagates_cash_selection_provenance() -> None:
    text = ACQUIRE.read_text()

    assert "cash_selection_provenance:" in text
    assert "steps.resolve.outputs.cash_selection_provenance" in text
    assert "selection_provenance_json:" in text
    assert "needs.resolve.outputs.cash_selection_provenance" in text
