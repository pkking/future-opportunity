"""Policy contracts for read-only native GitHub immutable Release auditing."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
WF = ROOT / ".github/workflows/audit-funding-vps-github-release.yml"


def test_only_release_published_trigger_with_explicit_read_permissions():
    text = WF.read_text()
    assert "  release:" in text and "    types: [published]" in text
    assert "  schedule:" not in text
    assert "  push:" not in text
    assert "  workflow_dispatch:" not in text
    assert "permissions:\n  contents: read" in text
    assert "  contents: write" not in text
    assert "  actions: write" not in text
    assert "  id-token: write" not in text
    assert "  attestations: write" not in text
    assert "  persist-credentials: false" in text


def test_audit_checks_exact_tag_release_integrity_and_original_bytes():
    text = WF.read_text()
    assert "if: startsWith(github.event.release.tag_name, 'funding-vps-')" in text
    assert "RELEASE_TAG: ${{ github.event.release.tag_name }}" in text
    assert "funding-vps-[0-9]{4}-[0-9]{2}-[0-9]{2}$" in text
    assert "gh release verify \"$RELEASE_TAG\"" in text
    assert "gh release verify-asset \"$RELEASE_TAG\"" in text
    assert "gh release download \"$RELEASE_TAG\"" in text
    assert "--pattern original-source.zip" in text
    assert "scripts/audit_github_vps_release.py" in text
    assert "original-source.zip" in text
    assert "offline-source-review.json" in text
    assert "provenance-review.json" in text


def test_failure_is_unassessed_and_original_archive_never_uploaded_as_actions_artifact():
    text = WF.read_text()
    assert "if: failure()" in text
    assert '"status":"UNASSESSED"' in text
    assert '"github_release_attestation_verified":false' in text
    assert '"point_in_time_publication_verified":false' in text
    assert '"acquisition_approved":false' in text
    assert '"promotion_approved":false' in text
    assert "retention-days: 90" in text
    assert "artifacts/github-vps-release-review/" in text
    assert "path: artifacts/github-vps-release-original/" not in text
    assert '"github_release_attestation_verified": True' in text
    assert '"point_in_time_publication_verified": False' in text
    assert '"promotion_approved": False' in text
    assert "on:\n  release:" in text
    assert "github-vps-funding-release-review" in text
    assert "github-vps-release-original" in text


def test_no_new_market_capture_or_github_release_write_actions():
    text = WF.read_text()
    forbidden = (
        "capture_funding_preentry_source.py",
        "run_vps_funding_preentry.py",
        "publish_vps_funding_github_release.py",
        "gh release create",
        "gh release upload",
        "gh release edit",
        "gh release delete",
        "curl -X POST",
        "gh api -X PATCH",
    )
    for phrase in forbidden:
        assert phrase not in text
    assert "GH_TOKEN: ${{ github.token }}" in text
    assert "--repo \"$GITHUB_REPOSITORY\"" in text
