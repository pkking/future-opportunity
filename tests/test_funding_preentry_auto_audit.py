"""Offline run/artifact identity, signed subject and failed capture proof."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from future_opportunity.backtest.funding_asof_capture import validate_preentry_source
from test_funding_asof_capture import _base

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/audit_scheduled_funding_capture.py"
WORKFLOW = ROOT / ".github/workflows/capture-funding-preentry-scheduled.yml"
SHA = "a" * 40
RUN = 91732
REPO = "pkking/future-opportunity"


def _auditor(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("scheduled_funding_auditor", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run():
    return {
        "id": RUN, "event": "schedule", "run_attempt": 1,
        "head_sha": SHA, "head_branch": "main",
        "path": ".github/workflows/capture-funding-preentry-scheduled.yml",
        "head_repository": {"full_name": REPO},
        "created_at": "2026-09-14T23:37:00Z",
    }


def _source_zip(tmp_path, *, success=True):
    path = tmp_path / "original.zip"
    if success:
        raw, timing = _base()
        report = validate_preentry_source(raw, timing)
        members = {
            "raw-api-capture.json": raw,
            "http-timing.json": timing,
            "preentry-research-evidence.json": report,
        }
    else:
        members = {"error.json": {
            "status": "UNASSESSED",
            "reason": "UTC entry cutoff missed",
            "point_in_time_publication_verified": False,
            "acquisition_approved": False,
            "promotion_approved": False,
        }}
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, json.dumps(data, sort_keys=True) + "\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return path, digest


def _inventory(digest):
    return {"artifacts": [{
        "id": 5643, "name": "prospective-funding-preentry-source",
        "size_in_bytes": 1234, "expired": False,
        "digest": "sha256:" + digest,
        "workflow_run": {
            "id": RUN, "head_sha": SHA, "head_branch": "main",
        },
    }]}


def _verify(raw, *, repository, sha):
    assert repository == REPO and sha == SHA
    return {
        "github_attestation_verified": True,
        "raw_file_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _audit(auditor, path, digest, **updates):
    settings = {
        "run": _run(), "inventory": _inventory(digest), "repository": REPO,
        "run_id": RUN, "source_sha": SHA, "capture_conclusion": "success",
        "verifier": _verify,
    }
    settings.update(updates)
    return auditor.audit_scheduled_capture(path, **settings)


def test_complete_read_only_success_is_not_okx_publication_proof(monkeypatch, tmp_path):
    auditor = _auditor(monkeypatch)
    path, digest = _source_zip(tmp_path)
    result = _audit(auditor, path, digest)
    assert result["status"] == "offline_replay_and_github_provenance_verified_only"
    assert result["entry_market_date"] == "2026-09-15"
    assert result["original_zip_sha256"] == digest
    assert result["github_attestation_verified"] is True
    assert len(result["raw_file_sha256"]) == 64
    assert result["exchange_signed"] is False
    assert result["point_in_time_publication_verified"] is False
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False


@pytest.mark.parametrize(("field", "value"), [
    ("id", 123), ("event", "workflow_dispatch"), ("run_attempt", 2),
    ("head_sha", "b" * 40), ("head_branch", "another"),
    ("path", ".github/workflows/capture-funding-preentry-source.yml"),
    ("created_at", "2026-09-15T08:00:00Z"),
    ("created_at", "2026-09-15T00:15:00Z"),
    ("created_at", "2026-09-14T22:15:00Z"),
])
def test_no_cross_run_or_backdated_capture_identity(monkeypatch, tmp_path, field, value):
    auditor = _auditor(monkeypatch)
    path, digest = _source_zip(tmp_path)
    run = _run()
    run[field] = value
    with pytest.raises(ValueError, match="identity|time"):
        _audit(auditor, path, digest, run=run)


def test_no_wrong_head_repo_metadata_or_duplicate_artifacts(monkeypatch, tmp_path):
    auditor = _auditor(monkeypatch)
    path, digest = _source_zip(tmp_path)
    run = _run()
    run["head_repository"] = {"full_name": "attacker/future-opportunity"}
    with pytest.raises(ValueError, match="identity"):
        _audit(auditor, path, digest, run=run)
    inventory = _inventory(digest)
    inventory["artifacts"].append(dict(inventory["artifacts"][0]))
    with pytest.raises(ValueError, match="exactly one"):
        _audit(auditor, path, digest, inventory=inventory)


def test_no_unsigned_or_tampered_archive(monkeypatch, tmp_path):
    auditor = _auditor(monkeypatch)
    path, digest = _source_zip(tmp_path)
    with pytest.raises(ValueError, match="digest mismatch"):
        _audit(auditor, path, "0" * 64)
    inventory = _inventory(digest)
    inventory["artifacts"][0]["workflow_run"]["id"] = RUN + 1
    with pytest.raises(ValueError, match="identity"):
        _audit(auditor, path, digest, inventory=inventory)
    with pytest.raises(ValueError, match="verification is incomplete"):
        _audit(auditor, path, digest, verifier=lambda *_args, **_kw: {
            "github_attestation_verified": False, "raw_file_sha256": digest,
        })


def test_failed_capture_is_an_unassessed_error_not_an_empty_market(monkeypatch, tmp_path):
    auditor = _auditor(monkeypatch)
    path, digest = _source_zip(tmp_path, success=False)

    def forbidden(*_args, **_kwargs):
        pytest.fail("must never verify an attestation on failed capture")

    result = _audit(
        auditor, path, digest, capture_conclusion="failure", verifier=forbidden,
    )
    assert result["status"] == "failed_capture_unassessed"
    assert result["github_attestation_verified"] is False
    assert result["point_in_time_publication_verified"] is False
    assert result["acquisition_approved"] is False
    assert "UTC entry" in result["failure_reason"]


def test_forged_failure_receipt_does_not_pass(monkeypatch, tmp_path):
    auditor = _auditor(monkeypatch)
    path, _ = _source_zip(tmp_path, success=False)
    forged = {
        "status": "UNASSESSED", "reason": "wrong",
        "point_in_time_publication_verified": True,
        "acquisition_approved": False, "promotion_approved": False,
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("error.json", json.dumps(forged))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="unsupported status"):
        _audit(auditor, path, digest, capture_conclusion="failure")
    with pytest.raises(ValueError, match="unapproved scheduled capture conclusion"):
        _audit(auditor, path, digest, capture_conclusion="cancelled")


def test_gh_verifier_checks_exact_signer_sha_ref_and_raw_subject(monkeypatch):
    auditor = _auditor(monkeypatch)
    raw = b'{"raw":"some original bytes"}\n'
    digest = hashlib.sha256(raw).hexdigest()
    captured = []

    def invoke(argv, **kwargs):
        captured.extend(argv)
        assert kwargs["check"] is True
        assert kwargs["timeout"] == 60
        assert Path(argv[3]).read_bytes() == raw
        return SimpleNamespace(stdout=json.dumps([{
            "verificationResult": {"statement": {
                "subject": [{"digest": {"sha256": digest}}],
            }},
        }]))

    monkeypatch.setattr(auditor.subprocess, "run", invoke)
    result = auditor.verify_github_attestation(raw, repository=REPO, sha=SHA)
    assert result["raw_file_sha256"] == digest
    assert result["github_attestation_verified"] is True
    assert "--repo" in captured and REPO in captured
    assert "--source-ref" in captured and "refs/heads/main" in captured
    assert "--source-digest" in captured and SHA in captured
    assert "--signer-workflow" in captured
    assert f"{REPO}/.github/workflows/capture-funding-preentry-scheduled.yml" in captured

    def forged(*_args, **_kw):
        return SimpleNamespace(stdout=json.dumps([{
            "verificationResult": {"statement": {
                "subject": [{"digest": {"sha256": "0" * 64}}],
            }},
        }]))

    monkeypatch.setattr(auditor.subprocess, "run", forged)
    with pytest.raises(ValueError, match="subject digest mismatch"):
        auditor.verify_github_attestation(raw, repository=REPO, sha=SHA)

    def fail(*_args, **_kw):
        raise subprocess.CalledProcessError(1, "gh")

    monkeypatch.setattr(auditor.subprocess, "run", fail)
    with pytest.raises(ValueError, match="signed raw-subject"):
        auditor.verify_github_attestation(raw, repository=REPO, sha=SHA)


def test_read_only_workflow_downloads_original_zip_and_reports_failures():
    wf = WORKFLOW.read_text()
    source = SCRIPT.read_text()
    assert "schedule:" in wf and "cron: '37 23 * * *'" in wf
    assert "workflow_dispatch:" not in wf and "  push:" not in wf
    assert "name: Audit scheduled source artifact (read-only)" in wf
    assert "needs: capture" in wf
    assert "github.run_attempt == 1" in wf
    assert "actions/download-artifact@v8" in wf
    assert "skip-decompress: true" in wf and "digest-mismatch: error" in wf
    assert 'gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"' in wf
    assert 'gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}/artifacts"' in wf
    assert "attestations: read" in wf and "actions: read" in wf
    assert "if: always()" in wf
    assert "scheduled-funding-evidence-review" in wf
    assert "client.get(" not in source and "client.post(" not in source
    assert "audit_zip(" in source and "gh" in source
