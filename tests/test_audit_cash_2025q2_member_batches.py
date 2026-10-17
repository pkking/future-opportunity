from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "member_artifact_audit", ROOT / "scripts/audit_cash_2025q2_member_batches.py"
)
assert spec and spec.loader
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


def fake_research_bundle(tmp_path, monkeypatch):
    days = audit_module.expected_dates()
    catalog = {}
    for day in days:
        catalog[day + "/FUTURES"] = {
            "sha256": "1" * 64,
            "response": {"data": [{"details": [{"groupDetails": [{
                "url": "https://static.okx.com/source/" + day,
            }]}]}]},
        }
    monkeypatch.setattr(
        audit_module, "audit",
        lambda path, sha: {"verified_calendar_dates": 90},
    )
    monkeypatch.setattr(
        audit_module, "extract_zip",
        lambda path, sha: (catalog, {}),
    )
    manifest = {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_exact_member_artifacts_manifest",
        "source_catalog_run": "39038071038",
        "source_catalog_artifact_id": "12103210971",
        "source_catalog_sha256": audit_module.PINNED_CATALOG_SHA,
        "member_source_run": "39045070860",
        "member_source_head_sha": "b5980b907d8e698906ef4fe49de18fba6b451cf6",
        "batches": [],
    }
    reports = []
    for batch_index in range(9):
        items = []
        for day in audit_module.dates_for_batch(batch_index):
            other = day == days[0]
            instrument = "BTC-USDT-250926" if other else audit_module.FUTURE_ID
            member = f"{instrument}-L2orderbook-400lv-{day}.data"
            items.append({
                "market_date": day,
                "future_id": audit_module.FUTURE_ID,
                "catalog_response_sha256": "1" * 64,
                "official_archive_url": "https://static.okx.com/source/" + day,
                "archive_sha256": "2" * 64,
                "archive_downloaded_bytes": 500,
                "archive_members": [member],
                "member_instrument_ids": [instrument],
                "matching_exact_contract_member_count": 0 if other else 1,
                "exact_contract_member": None if other else member,
                "member_status": "unavailable" if other else "identity_verified",
                "member_identity_verified": not other,
                "l2_orderbook_verified": False,
                "economic_returns_evaluated": False,
                "acquisition_approved": False,
                "promotion_approved": False,
            })
        counts = {
            label: sum(row["member_status"] == label for row in items)
            for label in ("identity_verified", "unavailable", "ambiguous", "error")
        }
        report = {
            "schema_version": 1,
            "evidence_type": "cash_2025q2_exact_futures_member_population_batch",
            "future_id": audit_module.FUTURE_ID,
            "source_zip_sha256": audit_module.PINNED_CATALOG_SHA,
            "batch_index": batch_index,
            "calendar_dates": list(audit_module.dates_for_batch(batch_index)),
            "complete": True,
            "status_counts": counts,
            "research_only": True,
            "outcome_blind": True,
            "l2_orderbook_verified": False,
            "sample_selection_frozen": False,
            "economic_returns_evaluated": False,
            "acquisition_approved": False,
            "promotion_approved": False,
            "observations": items,
        }
        reports.append(report)
    def flush():
        for i, report in enumerate(reports):
            name = f"cash-2025q2-exact-members-batch-{i}"
            output = tmp_path / (name + ".zip")
            with zipfile.ZipFile(output, "w") as zipfile_out:
                zipfile_out.writestr(f"member-batch-{i:02d}.json", json.dumps(report))
            sha = hashlib.sha256(output.read_bytes()).hexdigest()
            if len(manifest["batches"]) <= i:
                manifest["batches"].append({
                    "batch_index": i, "artifact_id": 1000 + i,
                    "artifact_name": name, "zip_sha256": sha,
                })
            else:
                manifest["batches"][i]["zip_sha256"] = sha
    flush()
    return manifest, reports, flush


def test_verified_full_population_is_source_only(tmp_path, monkeypatch):
    manifest, _, _ = fake_research_bundle(tmp_path, monkeypatch)
    result = audit_module.audit_population(tmp_path / "original.zip", manifest, tmp_path)
    assert result["complete_member_population_verified"] is True
    assert result["counts"]["identity_verified"] == 89
    assert result["counts"]["unavailable"] == 1
    assert result["source_unavailable_dates"] == ["2025-03-29"]
    assert len(result["verified_member_available_dates"]) == 89
    assert result["sample_selection_frozen"] is False
    assert result["acquisition_approved"] is False


def test_missing_artifact_is_not_an_empty_day(tmp_path, monkeypatch):
    manifest, _, _ = fake_research_bundle(tmp_path, monkeypatch)
    (tmp_path / "cash-2025q2-exact-members-batch-3.zip").unlink()
    with pytest.raises(FileNotFoundError):
        audit_module.audit_population(tmp_path / "original.zip", manifest, tmp_path)


def test_artifact_byte_tamper_is_rejected(tmp_path, monkeypatch):
    manifest, _, _ = fake_research_bundle(tmp_path, monkeypatch)
    p = tmp_path / "cash-2025q2-exact-members-batch-3.zip"
    p.write_bytes(p.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="SHA"):
        audit_module.audit_population(tmp_path / "original.zip", manifest, tmp_path)


@pytest.mark.parametrize("change", [
    lambda report: report.update({"sample_selection_frozen": True}),
    lambda report: report["observations"][0].update({"member_identity_verified": False}),
    lambda report: report["observations"][0].update({"catalog_response_sha256": "3" * 64}),
    lambda report: report["observations"][0].update({"archive_members": []}),
    lambda report: report["observations"].pop(),
    lambda report: report.update({"promotion_approved": True}),
])
def test_invalid_data_fails_even_when_artifact_digest_is_updated(
    tmp_path, monkeypatch, change
):
    manifest, reports, flush = fake_research_bundle(tmp_path, monkeypatch)
    change(reports[0])
    flush()
    with pytest.raises((ValueError, TypeError)):
        audit_module.audit_population(tmp_path / "original.zip", manifest, tmp_path)
