from pathlib import Path


ROOT = Path(__file__).parents[1]
COMPOSER = ROOT / ".github/workflows/compose-historical-acquisition.yml"


def test_acquisition_composer_workflow_is_read_only_and_never_dispatches_acquisition() -> None:
    text = COMPOSER.read_text()

    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "gh workflow run" not in text
    assert "workflow_dispatch" in text
    assert "Acquire Historical Campaign" not in text
    assert "git push" not in text
    assert "gh pr create" not in text


def test_acquisition_composer_verifies_exact_successful_case_plan_artifact() -> None:
    text = COMPOSER.read_text()

    assert "CASH_PLAN_RUN_ID" in text
    assert "CASH_PLAN_ARTIFACT_NAME" in text
    assert "test "$(jq -r '.status'" in text
    assert '= "completed"' in text
    assert "test "$(jq -r '.conclusion'" in text
    assert '= "success"' in text
    assert ".digest" in text
    assert ".expired" in text
    assert "gh run download" in text
    assert "37477835622" in text
    assert "cash-acquisition-case-plan-37477835622" in text
