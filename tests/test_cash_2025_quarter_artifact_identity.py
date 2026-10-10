"""Frozen Cash 2025 quarter artifact inventory and operator boundary tests."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.verify_cash_2025_quarter_artifacts import verify_inventory


ROOT = Path(__file__).parents[1]
PLANS = ROOT / "docs/historical-acquisition-plans"
WORKFLOW = ROOT / ".github/workflows/prepare-cash-2025-quarter-wave.yml"
SCRIPT = ROOT / "scripts/verify_cash_2025_quarter_artifacts.py"
RUN_ID = "38000000123"


def make_inputs(wave: str) -> tuple[dict, dict]:
    manifest = json.loads(
        (PLANS / f"cash-2025-{wave}-12day-wave-001.json").read_text()
    )
    records = []
    for case in manifest["cash_cases"]:
        date = case["entry_at"][:10]
        future = case["future_id"]
        suffix = f"{date}-{future}-{RUN_ID}"
        names = (
            f"okx-btc-cash-and-carry-{suffix}",
            f"okx-btc-cash-and-carry-compact-{suffix}",
            f"okx-btc-cash-and-carry-actuals-{suffix}",
        )
        for name in names:
            records.append(
                {
                    "id": 1000000 + len(records),
                    "name": name,
                    "size_in_bytes": 2048,
                    "digest": "sha256:" + ("a" * 64),
                    "expired": False,
                    "workflow_run": {"id": int(RUN_ID)},
                }
            )
    # A legitimate acquisition run also uploads a control artifact.
    records.append(
        {
            "id": 900999,
            "name": "historical-acquisition-control",
            "size_in_bytes": 4096,
            "digest": "sha256:" + ("b" * 64),
            "expired": False,
            "workflow_run": {"id": int(RUN_ID)},
        }
    )
    return manifest, {"total_count": len(records), "artifacts": records}


@pytest.mark.parametrize("wave", ["q3", "q4"])
def test_exact_twelve_by_three_artifacts_are_inventory_verified(wave: str) -> None:
    manifest, listing = make_inputs(wave)
    report = verify_inventory(manifest, listing, wave=wave, run_id=RUN_ID)

    assert report["status"] == "verified_inventory_only"
    assert not report["errors"]
    assert len(report["artifacts_by_market_date"]) == 12
    assert report["verified_artifact_count_by_kind"] == {
        "prepared": 12, "compact": 12, "actuals": 12,
    }
    assert not report["missing_artifact_names"]
    assert report["artifact_contents_verified"] is False
    assert report["l2_completeness_verified"] is False
    assert report["actuals_contents_verified"] is False
    assert report["corpus_mutation"] is False
    assert report["promotion_dispatched"] is False


@pytest.mark.parametrize("missing_kind", ["", "compact-", "actuals-"])
def test_missing_any_kind_fails_even_when_compact_count_is_twelve(
    missing_kind: str,
) -> None:
    manifest, listing = make_inputs("q3")
    match = "okx-btc-cash-and-carry-" + missing_kind
    listing["artifacts"] = [
        item for item in listing["artifacts"] if not item["name"].startswith(match)
    ][:] if missing_kind else [
        item for item in listing["artifacts"]
        if not (
            item["name"].startswith("okx-btc-cash-and-carry-")
            and "-compact-" not in item["name"]
            and "-actuals-" not in item["name"]
        )
    ]
    listing["total_count"] = len(listing["artifacts"])

    report = verify_inventory(manifest, listing, wave="q3", run_id=RUN_ID)
    assert report["status"] == "failed"
    assert report["missing_artifact_names"]


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("expired", True),
        ("expired", None),
        ("size_in_bytes", 0),
        ("size_in_bytes", -1),
        ("digest", None),
        ("digest", "sha256:abcd"),
        ("workflow_run", {"id": 12}),
        ("workflow_run", None),
        ("id", 0),
    ],
)
def test_invalid_artifact_metadata_fails(field: str, bad: object) -> None:
    manifest, listing = make_inputs("q3")
    listing["artifacts"][0][field] = bad

    report = verify_inventory(manifest, listing, wave="q3", run_id=RUN_ID)
    assert report["status"] == "failed"
    assert report["errors"]


def test_duplicate_names_fail_even_if_counts_do_not_change() -> None:
    manifest, listing = make_inputs("q3")
    listing["artifacts"][1]["name"] = listing["artifacts"][0]["name"]

    report = verify_inventory(manifest, listing, wave="q3", run_id=RUN_ID)
    assert report["status"] == "failed"
    assert any("duplicate artifact name" in error for error in report["errors"])


def test_duplicate_artifact_ids_fail() -> None:
    manifest, listing = make_inputs("q3")
    listing["artifacts"][1]["id"] = listing["artifacts"][0]["id"]

    report = verify_inventory(manifest, listing, wave="q3", run_id=RUN_ID)
    assert report["status"] == "failed"
    assert any("duplicate artifact id" in error for error in report["errors"])


def test_wrong_future_or_run_id_is_unexpected_and_missing() -> None:
    manifest, listing = make_inputs("q3")
    listing["artifacts"][0]["name"] = listing["artifacts"][0]["name"].replace(
        "BTC-USDT-250926", "BTC-USDT-251226"
    )

    report = verify_inventory(manifest, listing, wave="q3", run_id=RUN_ID)
    assert report["status"] == "failed"
    assert len(report["unexpected_artifact_names"]) == 1
    assert len(report["missing_artifact_names"]) == 1


def test_incomplete_pagination_fails_closed() -> None:
    manifest, listing = make_inputs("q3")
    listing["total_count"] += 1
    report = verify_inventory(manifest, listing, wave="q3", run_id=RUN_ID)
    assert report["status"] == "failed"
    assert any("all pages" in error for error in report["errors"])


def test_acquisition_job_failure_does_not_become_completion() -> None:
    manifest, listing = make_inputs("q3")
    report = verify_inventory(
        manifest, listing, wave="q3", run_id=RUN_ID,
        acquisition_result="failure",
    )
    assert report["status"] == "failed"
    assert any("acquisition job result" in e for e in report["errors"])


@pytest.mark.parametrize("mutation", ["future", "dates", "source", "cases", "wave"])
def test_frozen_manifest_drift_fails_closed(mutation: str) -> None:
    manifest, listing = make_inputs("q3")
    manifest = copy.deepcopy(manifest)
    if mutation == "future":
        manifest["cash_cases"][0]["future_id"] = "BTC-USDT-251226"
    elif mutation == "dates":
        manifest["cash_cases"][0]["entry_at"] = "2025-07-05T00:15:00+00:00"
    elif mutation == "source":
        manifest["selection_provenance"]["cash"]["source"]["artifact_id"] = "1"
    elif mutation == "cases":
        manifest["cash_cases"] = manifest["cash_cases"][:-1]
    else:
        manifest["acquisition_id"] = "not-approved"
    report = verify_inventory(manifest, listing, wave="q3", run_id=RUN_ID)
    assert report["status"] == "failed"
    assert any("frozen manifest invalid" in e for e in report["errors"])


def test_invalid_listing_fails_closed() -> None:
    manifest, _ = make_inputs("q3")
    report = verify_inventory(manifest, {"unexpected": []}, wave="q3", run_id=RUN_ID)
    assert report["status"] == "failed"


def test_cli_writes_failed_report_to_disk(tmp_path: Path) -> None:
    manifest, listing = make_inputs("q3")
    listing["artifacts"] = []
    listing["total_count"] = 0
    manifest_file = tmp_path / "manifest.json"
    artifacts_file = tmp_path / "artifacts.json"
    output = tmp_path / "audit" / "summary.json"
    manifest_file.write_text(json.dumps(manifest))
    artifacts_file.write_text(json.dumps(listing))
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--manifest", str(manifest_file),
            "--artifacts", str(artifacts_file),
            "--wave", "q3",
            "--run-id", RUN_ID,
            "--acquisition-result", "failure",
            "--output", str(output),
        ],
        check=False, capture_output=True, text=True,
    )
    assert result.returncode == 1
    saved = json.loads(output.read_text())
    assert saved["status"] == "failed"
    assert len(saved["missing_artifact_names"]) == 36


def test_2025_workflow_gates_manifest_and_preserves_failure_evidence() -> None:
    text = WORKFLOW.read_text()
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "contents: read" in text
    assert "actions: read" in text
    assert "contents: write" not in text
    assert "prepare-cash-2025-quarter-wave.yml" not in text.split("uses: ./")[0]
    assert "verify_cash_2025_quarter_artifacts.py" in text
    assert "--acquisition-result" in text
    assert "if: always()" in text
    assert "corpus_mutation" not in text or "promotion_dispatched" not in text
    assert "promote-historical" not in text
