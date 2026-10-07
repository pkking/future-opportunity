from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/review-pending-historical-prs.yml"


def test_pending_pr_review_workflow_is_read_only_and_bounded() -> None:
    source = WORKFLOW.read_text()

    assert "contents: read" in source
    assert "pull-requests: read" in source
    assert "contents: write" not in source
    assert "pull-requests: write" not in source
    assert "gh pr create" not in source
    assert "gh pr merge" not in source
    assert "git push" not in source
    assert "git checkout" not in source
    assert "per_page=100" in source
    assert "ref=${head_sha}" in source

    assert "report_pending_corpus_prs.py" in source
    assert "tests/fixtures/historical/corpus-index.json" in source
    assert "actions/upload-artifact@v4" in source
    assert "if: always()" in source
    assert "proposals/pr-${pr_number}.json" in source
