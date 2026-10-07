from pathlib import Path


ROOT = Path(__file__).parents[1]
PROMOTE = ROOT / ".github/workflows/promote-historical-campaign.yml"
PLANNED = ROOT / ".github/workflows/promote-planned-historical-wave.yml"


def test_campaign_promotion_is_reusable_without_weakening_review_boundary() -> None:
    text = PROMOTE.read_text()

    assert "workflow_call:" in text
    assert "campaign_json:" in text
    assert "contents: write" in text
    assert "pull-requests: write" in text
    assert "git switch -c" in text
    assert "git push --set-upstream origin" in text
    assert "gh pr create" in text
    assert "repository_policy_blocks_actions_pr_creation" in text
    assert "git push origin main" not in text
    assert "gh pr merge" not in text


def test_planned_wave_handoff_requires_exact_successful_planner_evidence() -> None:
    text = PLANNED.read_text()

    assert "workflow_dispatch:" in text
    assert "push:" not in text
    assert "planner_run_id:" in text
    assert "planner_artifact_name:" in text
    assert "wave_file:" in text
    assert "Plan Historical Corpus Campaign" in text
    assert "completed" in text
    assert "success" in text
    assert "artifacts?per_page=100" in text
    assert "gh run download" in text
    assert ".wave_files | index($file) != null" in text
    assert "item_count" in text
    assert "-le 31" in text


def test_planned_wave_handoff_calls_single_campaign_promotion_implementation() -> None:
    text = PLANNED.read_text()

    assert "uses: ./.github/workflows/promote-historical-campaign.yml" in text
    assert "needs.resolve.outputs.campaign_json" in text
    assert "tests/fixtures/historical" not in text
    assert "git push" not in text
    assert "gh pr create" not in text
