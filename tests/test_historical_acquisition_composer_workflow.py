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
    assert ".status" in text
    assert "completed" in text
    assert ".conclusion" in text
    assert "success" in text
    assert ".digest" in text
    assert ".expired" in text
    assert "gh run download" in text
    assert "37477835622" in text
    assert "cash-acquisition-case-plan-37477835622" in text


def test_acquisition_composer_verifies_exact_successful_sampling_artifact() -> None:
    text = COMPOSER.read_text()

    assert "FUNDING_SAMPLE_RUN_ID" in text
    assert "FUNDING_SAMPLE_ARTIFACT_NAME" in text
    assert "37482498880" in text
    assert "historical-market-day-sample-37482498880" in text
    assert "sample.json" in text
    assert "--funding-sample" in text


def test_push_selftest_defaults_do_not_leak_into_manual_dispatch_inputs() -> None:
    text = COMPOSER.read_text()

    assert "github.event_name == 'push'" in text
    assert "FUNDING_START_DATE: ${{ inputs.funding_start_date }}" in text
    assert "FUNDING_END_DATE: ${{ inputs.funding_end_date }}" in text
    assert (
        "github.event_name == 'push' && '37482498880'"
        in text
    )
    assert (
        "github.event_name == 'push' && '37477835622'"
        in text
    )


def test_acquisition_composer_builds_and_consumes_selection_provenance() -> None:
    text = COMPOSER.read_text()

    assert "scripts/build_historical_selection_provenance.py" in text
    assert "--source-workflow-run" in text
    assert "--artifact-name" in text
    assert "--artifact-id" in text
    assert "--artifact-digest" in text
    assert "funding-selection-provenance.json" in text
    assert "--funding-selection-provenance" in text
    assert "selection_provenance_path" in text
