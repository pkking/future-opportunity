"""Offline cross-host VPS source receipt validation: evidence, never promotion."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from future_opportunity.backtest.funding_asof_capture import validate_preentry_source
from test_funding_asof_capture import _base

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/audit_vps_funding_capture.py"
DAY = "2026-09-15"
STARTED = "2026-09-15T00:00:11.208411+00:00"
REVIEW_TIME = datetime(2026, 10, 21, 10, 0, tzinfo=UTC)
PROD_2026_10_21 = {
    "archive_sha256": "6adc7385b4e32aabd886abf27b53446c1ecab1b00ec23f664b69861a149bfd3a",
    "raw_file_sha256": "5e753951d8317eb1e32265554d17b13cc515d293dda6108690f7c2f3a4828c0e",
    "canonical_source_sha256": "88365202bc78791c4cc8f2339cb356ea44f9fc36551ba065280affbefe813609",
    "entry_market_date": "2026-10-21",
    "regime": "nonnegative_low_volatility",
    "started_at": "2026-10-21T00:00:11.208411+00:00",
}


def _auditor(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("funding_vps_receipt_audit", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _files(tmp_path, *, fail=False):
    archive = tmp_path / "original-source.zip"
    if fail:
        error = {
            "status": "UNASSESSED",
            "reason": "VPS NTP clock is not confirmed synchronized",
            "error_type": "ValueError",
            "point_in_time_publication_verified": False,
            "acquisition_approved": False,
            "promotion_approved": False,
        }
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("error.json", json.dumps(error) + "\n")
    else:
        raw, timing = _base()
        evidence = validate_preentry_source(raw, timing)
        with zipfile.ZipFile(archive, "w") as z:
            for name, value in (
                ("raw-api-capture.json", raw),
                ("http-timing.json", timing),
                ("preentry-research-evidence.json", evidence),
            ):
                z.writestr(name, json.dumps(value, sort_keys=True) + "\n")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "origin": "vps_systemd_local_only",
        "started_at": STARTED,
        "intended_utc_day": DAY,
        "status": "UNASSESSED" if fail else "local_replay_only",
        "archive_sha256": digest,
        "entry_market_date": None if fail else DAY,
        "files": ["error.json"] if fail else [
            "raw-api-capture.json", "http-timing.json", "preentry-research-evidence.json",
        ],
        "github_attestation_verified": False,
        "exchange_signed": False,
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
    }
    if fail:
        manifest["reason"] = error["reason"]
    else:
        with zipfile.ZipFile(archive) as z:
            manifest["raw_file_sha256"] = hashlib.sha256(
                z.read("raw-api-capture.json")
            ).hexdigest()
        manifest["canonical_source_sha256"] = evidence["raw_source_sha256"]
        manifest["regime"] = evidence["regime"]
    manifest_path = tmp_path / "manifest.json"
    _json(manifest_path, manifest)
    return manifest_path, archive, digest, manifest


def _review(module, manifest, archive, digest, day=DAY):
    return module.audit_vps_receipt(
        manifest, archive, expected_zip_sha256=digest,
        expected_entry_date=day, reviewed_at=lambda: REVIEW_TIME,
    )


def test_success_has_exact_local_only_semantics_and_review_time(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, digest, _ = _files(tmp_path)
    result = _review(module, manifest, archive, digest)
    assert result["status"] == "offline_vps_replay_only"
    assert result["entry_market_date"] == DAY
    assert result["regime"] is not None
    assert result["expected_digest_match"] is True
    assert result["original_zip_sha256"] == digest
    assert result["manifest_sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert result["origin"] == "vps_systemd_local_only"
    assert result["reviewed_at"] == REVIEW_TIME.isoformat()
    assert result["review_time_is_capture_time"] is False
    assert result["expected_digest_origin_authenticated"] is False
    for key in (
        "github_attestation_verified", "exchange_signed",
        "point_in_time_publication_verified", "acquisition_approved",
        "promotion_approved",
    ):
        assert result[key] is False


def test_failure_is_error_only_without_market_date(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, digest, _ = _files(tmp_path, fail=True)
    result = _review(module, manifest, archive, digest)
    assert result["status"] == "failed_capture_unassessed"
    assert result["entry_market_date"] is None
    assert result["regime"] is None
    assert result["raw_file_sha256"] is None
    assert result["promotion_approved"] is False


@pytest.mark.parametrize("name,value,pattern", [
    ("origin", "github_actions_scheduled_source", "origin"),
    ("intended_utc_day", "2026-09-16", "origin"),
    ("github_attestation_verified", True, "approval"),
    ("exchange_signed", True, "approval"),
    ("point_in_time_publication_verified", True, "approval"),
    ("acquisition_approved", True, "approval"),
    ("promotion_approved", True, "approval"),
    ("entry_market_date", "2026-09-16", "market UTC"),
    ("status", "success", "unexpected state"),
    ("started_at", "2026-09-15T00:15:01+00:00", "outside"),
    ("started_at", "2026-09-15T00:00:01", "timezone"),
    ("started_at", "2026-09-16T00:00:01+00:00", "start on expected"),
    ("raw_file_sha256", "a" * 64, "disagrees"),
    ("canonical_source_sha256", "b" * 64, "disagrees"),
    ("regime", "negative_low_volatility", "disagrees"),
])
def test_rejects_forged_manifest_fields(monkeypatch, tmp_path, name, value, pattern):
    module = _auditor(monkeypatch)
    manifest, archive, digest, data = _files(tmp_path)
    data[name] = value
    _json(manifest, data)
    with pytest.raises(ValueError, match=pattern):
        _review(module, manifest, archive, digest)


def test_refuses_manifest_extra_missing_duplicate_fields(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, digest, data = _files(tmp_path)
    data["unexpected"] = 1
    _json(manifest, data)
    with pytest.raises(ValueError, match="unexpected"):
        _review(module, manifest, archive, digest)
    data.pop("unexpected")
    data.pop("files")
    _json(manifest, data)
    with pytest.raises(ValueError, match="unexpected"):
        _review(module, manifest, archive, digest)
    manifest.write_text(manifest.read_text().replace(
        '"origin": "vps_systemd_local_only",',
        '"origin": "vps_systemd_local_only", "origin": "vps_systemd_local_only",',
    ))
    with pytest.raises(ValueError, match="duplicate"):
        _review(module, manifest, archive, digest)


def test_requires_independent_digest_not_own_manifest_or_bytes(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, digest, _ = _files(tmp_path)
    with pytest.raises(ValueError, match="digest mismatch"):
        _review(module, manifest, archive, "a" * 64)
    with pytest.raises(ValueError, match="lowercase"):
        _review(module, manifest, archive, "not-a-hex-digest")
    with pytest.raises(ValueError, match="entry date"):
        _review(module, manifest, archive, digest, day="2026-09-16")
    with pytest.raises(ValueError, match="invalid"):
        _review(module, manifest, archive, digest, day="2026-13-16")
    archive.write_bytes(archive.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="digest mismatch"):
        _review(module, manifest, archive, digest)


def test_rejects_symlink_manifest_or_zip_and_oversized_manifest(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, digest, _ = _files(tmp_path)
    link = tmp_path / "fake-manifest"
    link.symlink_to(manifest)
    with pytest.raises(ValueError, match="ordinary file"):
        _review(module, link, archive, digest)
    ziplink = tmp_path / "fake-zip"
    ziplink.symlink_to(archive)
    with pytest.raises(ValueError, match="ordinary file"):
        _review(module, manifest, ziplink, digest)
    manifest.write_bytes(b" " * 65537)
    with pytest.raises(ValueError, match="bounded"):
        _review(module, manifest, archive, digest)


def test_rejects_repacked_wrong_or_duplicate_zip_entries(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, _, data = _files(tmp_path)
    with zipfile.ZipFile(archive, "a") as z:
        z.writestr("error.json", "{}")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    data["archive_sha256"] = digest
    _json(manifest, data)
    with pytest.raises(ValueError, match="exactly three"):
        _review(module, manifest, archive, digest)


def test_failure_receipt_rejects_false_success_and_extra_files(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, _, data = _files(tmp_path, fail=True)
    with zipfile.ZipFile(archive, "a") as z:
        z.writestr("raw-api-capture.json", "{}")
    new_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    data["archive_sha256"] = new_digest
    _json(manifest, data)
    with pytest.raises(ValueError, match="exactly error"):
        _review(module, manifest, archive, new_digest)
    manifest, archive, digest, data = _files(tmp_path, fail=True)
    data["entry_market_date"] = DAY
    _json(manifest, data)
    with pytest.raises(ValueError, match="must not claim"):
        _review(module, manifest, archive, digest)


def test_failure_receipt_cannot_claim_approval_in_inner_error(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, _, data = _files(tmp_path, fail=True)
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("error.json", json.dumps({
            "status": "UNASSESSED", "reason": data["reason"], "error_type": "ValueError",
            "point_in_time_publication_verified": True,
            "acquisition_approved": False, "promotion_approved": False,
        }))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    data["archive_sha256"] = digest
    _json(manifest, data)
    with pytest.raises(ValueError, match="cannot claim"):
        _review(module, manifest, archive, digest)


def test_exact_production_metadata_is_not_independent_zip_evidence(monkeypatch, tmp_path):
    module = _auditor(monkeypatch)
    manifest, archive, digest, data = _files(tmp_path)
    data.update(PROD_2026_10_21)
    data["intended_utc_day"] = "2026-10-21"
    _json(manifest, data)
    # Synthetic ZIP is intentionally NOT claimed as the actual production ZIP.
    with pytest.raises(ValueError, match="digest mismatch"):
        _review(module, manifest, archive, PROD_2026_10_21["archive_sha256"], day="2026-10-21")
    # Supplying our fixture ZIP digest also cannot silently authenticate
    # a different production manifest's asserted digest.
    with pytest.raises(ValueError, match="origin, day, digest"):
        _review(module, manifest, archive, digest, day="2026-10-21")


def test_new_review_receipt_never_overwrites(monkeypatch, tmp_path, capsys):
    module = _auditor(monkeypatch)
    manifest, archive, digest, _ = _files(tmp_path)
    receipt = tmp_path / "offhost-review.json"
    monkeypatch.setattr(sys, "argv", [
        "audit_vps_funding_capture.py", "--manifest", str(manifest),
        "--zip", str(archive), "--expected-zip-sha256", digest,
        "--entry-date", DAY, "--receipt-out", str(receipt),
    ])
    module.main()
    saved = receipt.read_bytes()
    assert json.loads(saved)["status"] == "offline_vps_replay_only"
    assert receipt.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        module.main()
    assert receipt.read_bytes() == saved


def test_reviewer_has_no_network_or_git_action_promotion_path():
    source = SCRIPT.read_text()
    assert "httpx" not in source
    assert "requests." not in source
    assert "subprocess.run" not in source
    assert "urllib.request" not in source
    assert "github.com" not in source
    assert "source_authentication_status" in source
    assert "expected_digest_origin_authenticated" in source
