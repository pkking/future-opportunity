"""Frozen existing-GitHub-Release diagnostic verification workflow invariants.

This test intentionally checks a single already-published immutable
diagnostic. It must never enable historical source capture/promotion.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/review-funding-diagnostic-release.yml"
SOURCE_ZIP = "6adc7385b4e32aabd886abf27b53446c1ecab1b00ec23f664b69861a149bfd3a"
SOURCE_MANIFEST = "96e16bde5e29e4c53360988c0f2a29ce1c0ce3727e2401fa779f16c1228d8fdb"
DIAGNOSTIC_TAG = "diagnostic-funding-vps-2026-10-21"


def test_diagnostic_workflow_is_read_only_and_no_source_refresh():
    s = WORKFLOW.read_text()
    assert "  workflow_dispatch:" in s
    assert "  push:\n    branches: [main]\n    paths:" in s
    assert ".github/workflows/review-funding-diagnostic-release.yml" in s
    assert "permissions:\n  contents: read" in s
    for unsafe in (
        "  schedule:",
        "  release:",
        "  contents: write",
        "  actions: write",
        "  id-token: write",
        "  attestations: write",
        "capture_funding_preentry_source.py",
        "run_vps_funding_preentry.py",
        "publish_vps_funding_github_release.py",
        "gh release create",
        "gh release edit",
        "gh release upload",
        "gh release delete",
        "gh workflow run",
        "curl -X POST",
    ):
        assert unsafe not in s
    assert "persist-credentials: false" in s
    assert "GH_TOKEN: ${{ github.token }}" in s


def test_reuses_exact_existing_release_and_original_digest_witness():
    s = WORKFLOW.read_text()
    assert f"TAG: {DIAGNOSTIC_TAG}" in s
    assert f"SOURCE_SHA256: {SOURCE_ZIP}" in s
    assert f"MANIFEST_SHA256: {SOURCE_MANIFEST}" in s
    assert "ENTRY_DAY: '2026-10-21'" in s
    assert "gh api \"repos/$REPO/releases/tags/$TAG\"" in s
    assert 'gh release download "$TAG"' in s
    assert "--pattern original-source.zip" in s
    assert "--pattern manifest.json" in s
    assert "sha256sum --check" in s
    assert 'gh release verify "$TAG"' in s
    assert 'gh release verify-asset "$TAG"' in s
    assert "scripts/audit_vps_funding_capture.py" in s
    assert "--expected-zip-sha256 \"$SOURCE_SHA256\"" in s


def test_release_is_explicitly_late_and_cannot_become_a_prospective_proof():
    s = WORKFLOW.read_text()
    assert "release[\"immutable\"] is True" in s
    assert "release[\"draft\"] is False" in s
    assert "release[\"prerelease\"] is True" in s
    assert 'parse_time("2026-10-21T00:15:00Z")' in s
    assert "published > start" in s
    assert '"diagnostic_only_github_hosted_offline_replay_verified"' in s
    assert '"github_hosted_preentry_source_verified": False' in s
    assert '"point_in_time_publication_verified": False' in s
    assert '"acquisition_approved": False' in s
    assert '"promotion_approved": False' in s
    assert '"exchange_signed": False' in s
    assert "github_release_attestation_cli_verified" in s
    assert "vps_original_offline_replay_verified" in s


def test_failure_replay_preserves_unassessed_and_source_is_not_reuploaded():
    s = WORKFLOW.read_text()
    assert "if: failure()" in s
    assert '\"status\":\"UNASSESSED\"' in s
    assert '\"acquisition_approved\":false' in s
    assert '\"promotion_approved\":false' in s
    assert "retention-days: 90" in s
    assert "path: artifacts/diagnostic-review/" in s
    assert "path: artifacts/diagnostic-originals/" not in s
    assert "funding-vps-existing-diagnostic-replay" in s
    assert 'if: always()' in s
    assert 'gh release verify-asset "$TAG"' in s
