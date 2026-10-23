"""Static policy: daily release absence watcher stays GitHub-only and read-only."""
from pathlib import Path

ROOT = Path(__file__).parents[1]
WF = ROOT / ".github/workflows/watch-funding-vps-release-health.yml"
SCRIPT = ROOT / "scripts/check_funding_release_watch.py"


def test_workflow_checks_after_utc_deadline_and_catches_cron_delay():
    s = WF.read_text()
    assert "  schedule:" in s
    assert "cron: '41 0 * * *'" in s
    assert "  workflow_dispatch:" in s
    assert "  push:\n    branches: [main]\n    paths:" in s
    assert ".github/workflows/watch-funding-vps-release-health.yml" in s
    assert "args=(--days 3" in s
    assert "--entry-day" in s
    assert "concurrency:" in s
    assert "cancel-in-progress: false" in s


def test_workflow_minimum_read_grants_and_no_market_source_or_repo_write():
    s = WF.read_text()
    assert "permissions:\n  contents: read\n  actions: read" in s
    assert "GH_TOKEN: ${{ github.token }}" in s
    assert "persist-credentials: false" in s
    assert "scripts/check_funding_release_watch.py" in s
    for forbidden in (
        "  contents: write", "  actions: write", "  id-token: write",
        "  attestations: write", "  release:", "gh release create",
        "gh release upload", "gh release edit", "gh release delete",
        "gh api -X POST", "curl -X POST", "run_vps_funding_preentry.py",
        "publish_vps_funding_github_release.py",
        "capture_funding_preentry_source.py",
    ):
        assert forbidden not in s


def test_fail_closed_artifact_and_no_raw_source_retention():
    s = WF.read_text()
    assert "if: failure()" in s
    assert '"status":"UNASSESSED"' in s
    assert '"point_in_time_publication_verified":false' in s
    assert '"acquisition_approved":false' in s
    assert '"promotion_approved":false' in s
    assert "if: always()" in s
    assert "actions/upload-artifact@v4" in s
    assert "retention-days: 90" in s
    assert "path: artifacts/funding-release-watch/" in s
    assert "path: artifacts/github-vps-release-original/" not in s
    assert "original-source.zip" not in s
    assert "funding-vps-daily-release-health" in s


def test_review_script_has_no_source_production_or_credential_writes():
    s = SCRIPT.read_text()
    assert "FIRST_DAY = date(2026, 10, 23)" in s
    assert "MISSING_PUBLISHED_RELEASE" in s
    assert "AUDIT_PENDING" in s and "AUDIT_FAILED" in s and "AUDIT_MISSING" in s
    assert "verify_release" in s
    assert "httpx.Client" in s
    assert '"point_in_time_publication_verified": False' in s
    assert '"acquisition_approved": False' in s
    assert '"promotion_approved": False' in s
    assert "client.get(" in s
    assert "client.post(" not in s
    assert "client.put(" not in s
    assert "client.patch(" not in s
    assert "client.delete(" not in s
    assert "api.okx.com" not in s
