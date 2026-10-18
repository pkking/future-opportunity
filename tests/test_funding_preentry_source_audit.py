"""Offline prospective Funding artifact audits never certify publication as-of entry."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from future_opportunity.backtest.funding_asof_capture import validate_preentry_source
from test_funding_asof_capture import _base

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/audit_funding_preentry_source_artifact.py"
MEMBERS = (
    "raw-api-capture.json",
    "http-timing.json",
    "preentry-research-evidence.json",
)


def _auditor():
    spec = importlib.util.spec_from_file_location("funding_preentry_audit", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _original(tmp_path: Path, *, raw=None, timing=None, evidence=None, extra=None):
    original_raw, original_timing = _base()
    raw = original_raw if raw is None else raw
    timing = original_timing if timing is None else timing
    evidence = validate_preentry_source(raw, timing) if evidence is None else evidence
    path = tmp_path / "original.zip"
    with zipfile.ZipFile(path, "w") as artifact:
        for name, value in zip(MEMBERS, (raw, timing, evidence), strict=True):
            artifact.writestr(name, json.dumps(value, sort_keys=True) + "\n")
        if extra:
            artifact.writestr(extra, "{}")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _audit(path: Path, digest: str, day="2026-09-15"):
    return _auditor().audit_zip(
        path, expected_zip_sha256=digest, expected_entry_date=day,
    )


def test_exact_artifact_replays_but_explicitly_denies_independent_publication(tmp_path):
    path, digest = _original(tmp_path)
    result = _audit(path, digest)
    assert result["status"] == "offline_replay_verified_only"
    assert result["archive_sha256"] == digest
    assert len(result["raw_file_sha256"]) == 64
    assert len(result["canonical_source_sha256"]) == 64
    assert result["raw_file_sha256"] != result["canonical_source_sha256"]
    assert result["http_transactions_completed_before_entry"] is True
    assert result["github_attestation_verified"] is False
    assert result["point_in_time_publication_verified"] is False
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False


def test_requires_independent_archive_digest_and_expected_utc_day(tmp_path):
    path, digest = _original(tmp_path)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _audit(path, "0" * 64)
    with pytest.raises(ValueError, match="lowercase hex"):
        _audit(path, "not-a-digest")
    with pytest.raises(ValueError, match="entry date"):
        _audit(path, digest, day="2026-09-16")
    with pytest.raises(ValueError, match="invalid"):
        _audit(path, digest, day="2026-13-15")


def test_rejects_extra_or_missing_or_duplicate_archive_files(tmp_path):
    path, digest = _original(tmp_path, extra="extra.json")
    with pytest.raises(ValueError, match="exactly three"):
        _audit(path, digest)
    path = tmp_path / "missing.zip"
    with zipfile.ZipFile(path, "w") as artifact:
        artifact.writestr("raw-api-capture.json", "{}")
    with pytest.raises(ValueError, match="exactly three"):
        _audit(path, hashlib.sha256(path.read_bytes()).hexdigest())
    path, _ = _original(tmp_path)
    with zipfile.ZipFile(path, "a") as artifact:
        artifact.writestr("raw-api-capture.json", "{}")
    with pytest.raises(ValueError, match="exactly three"):
        _audit(path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_rejects_oversized_and_corrupt_archive(tmp_path):
    path = tmp_path / "oversized.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as artifact:
        for name in MEMBERS:
            artifact.writestr(name, " " * 2_000_001)
    with pytest.raises(ValueError, match="oversized"):
        _audit(path, hashlib.sha256(path.read_bytes()).hexdigest())
    path.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="readable original"):
        _audit(path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_rejects_forged_evidence_and_late_source_even_when_zip_hash_matches(tmp_path):
    raw, timing = _base()
    evidence = validate_preentry_source(raw, timing)
    evidence["point_in_time_publication_verified"] = True
    path, digest = _original(tmp_path, raw=raw, timing=timing, evidence=evidence)
    with pytest.raises(ValueError, match="does not match"):
        _audit(path, digest)
    raw, timing = _base()
    timing["spot_response_received_at"] = "2026-09-15T00:15:01+00:00"
    path, digest = _original(tmp_path, raw=raw, timing=timing, evidence={})
    with pytest.raises(ValueError, match="before entry"):
        _audit(path, digest)


def test_offline_auditor_has_no_network_or_promotion_path():
    source = SCRIPT.read_text()
    assert "httpx" not in source and "requests." not in source
    assert "urllib.request" not in source and "client.get(" not in source
    assert "validate_preentry_source" in source
    assert "github_attestation_verified" in source
    assert "exchange_signed" in source
