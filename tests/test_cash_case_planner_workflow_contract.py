from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/plan-cash-acquisition-cases.yml"


def test_cash_case_planner_workflow_is_read_only() -> None:
    text = WORKFLOW.read_text()

    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "git push" not in text
    assert "gh pr create" not in text
    assert "uses: ./.github/workflows/prepare-" not in text
    assert "cash-history-discovery-" in text
    assert "plan_cash_acquisition_cases.py" in text
