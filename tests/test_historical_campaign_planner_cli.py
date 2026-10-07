from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from future_opportunity.backtest.campaign_inventory import (
    verified_candidates_from_inventory,
)


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests/fixtures/historical"
FUNDING = (
    FIXTURES
    / "okx-btc-usdt-funding-carry-2026-09-02-v1-target-compact"
)
CASH = (
    FIXTURES
    / "okx-btc-usdt-cash-and-carry-2026-06-02-BTC-USDT-260626-v1-target-compact"
)


def inventory_item(
    root: Path,
    *,
    run: str,
    name: str,
    compact_id: str,
    parent_id: str,
    parent_digest: str,
) -> dict[str, str]:
    return {
        "source_root": str(root),
        "source_workflow_run": run,
        "compact_artifact_name": name,
        "compact_artifact_id": compact_id,
        "compact_artifact_digest": "sha256:" + "a" * 64,
        "parent_artifact_id": parent_id,
        "parent_artifact_sha256": "sha256:" + parent_digest,
    }


def funding_inventory() -> dict[str, str]:
    return inventory_item(
        FUNDING,
        run="37327493270",
        name="okx-btc-funding-compact-2026-09-02",
        compact_id="11353595058",
        parent_id="11353260627",
        parent_digest=(
            "4eed3e2eac19b19aca29dd4ce76bc3f596d6b09a51c22d587b734825d520af74"
        ),
    )


def cash_inventory() -> dict[str, str]:
    return inventory_item(
        CASH,
        run="37327804191",
        name="okx-btc-cash-and-carry-compact-BTC-USDT-260626-37327804191",
        compact_id="11398999999",
        parent_id="11353125961",
        parent_digest=(
            "1d1ca77522befbc4fa2eb27c57fa15c15eb4915db50cf1fc08beb0c6f8fcfa31"
        ),
    )


def test_inventory_inspection_rejects_parent_source_mismatch(
    tmp_path: Path,
) -> None:
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "items": [funding_inventory()],
    }))
    candidates, evidence = verified_candidates_from_inventory(path)
    assert candidates[0].entry.strategy == "funding-carry"
    assert evidence[0]["entry_market_date"] == "2026-09-02"
    assert evidence[0]["selection_provenance_sha256"] == "absent"

    invalid = funding_inventory()
    invalid["parent_artifact_sha256"] = "sha256:" + "0" * 64
    path.write_text(json.dumps({
        "schema_version": 1,
        "items": [invalid],
    }))
    with pytest.raises(ValueError, match="parent artifact digest"):
        verified_candidates_from_inventory(path)


def test_cli_generates_review_wave_but_keeps_pinned_count_unchanged(
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "historical"
    fixture_root.mkdir()
    shutil.copytree(FUNDING, fixture_root / FUNDING.name)
    (fixture_root / "corpus-index.json").write_text(
        json.dumps({
            "schema_version": 1,
            "entries": [{
                "dataset_id": FUNDING.name,
                "strategy": "funding-carry",
                "entry_market_date": "2026-09-02",
                "fixture_path": FUNDING.name,
            }],
        }, indent=2)
        + "\n"
    )

    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(json.dumps({
        "schema_version": 1,
        "items": [cash_inventory(), funding_inventory()],
    }))
    output_dir = tmp_path / "planner-report"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/plan_historical_campaign.py",
            str(inventory_path),
            "--campaign-prefix",
            "test-review",
            "--fixture-root",
            str(fixture_root),
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    report = json.loads((output_dir / "report.json").read_text())
    assert report["does_not_promote"] is True
    assert report["pinned_counts"] == {
        "funding-carry": 1,
        "cash-and-carry": 0,
    }
    assert report["projected_counts_if_all_waves_merged"] == {
        "funding-carry": 1,
        "cash-and-carry": 1,
    }
    assert report["selected_count"] == 1
    assert report["excluded_pinned_count"] == 1
    wave_path = output_dir / report["wave_files"][0]
    wave = json.loads(wave_path.read_text())
    assert wave["campaign_id"] == "test-review-wave-001"
    assert wave["items"] == [{
        "source_workflow_run": "37327804191",
        "compact_artifact_name": (
            "okx-btc-cash-and-carry-compact-BTC-USDT-260626-37327804191"
        ),
    }]
    assert "test-review-wave-001" in completed.stdout
    assert not (fixture_root / CASH.name).exists()


def test_inventory_schema_rejects_missing_digest(tmp_path: Path) -> None:
    incoming = funding_inventory()
    del incoming["compact_artifact_digest"]
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps({"schema_version": 1, "items": [incoming]}))
    with pytest.raises(ValueError, match="fields differ from schema"):
        verified_candidates_from_inventory(path)


def test_planner_reports_pre_registered_candidate_over_legacy_pinned_day(
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "historical"
    fixture_root.mkdir()
    shutil.copytree(CASH, fixture_root / CASH.name)
    (fixture_root / "corpus-index.json").write_text(
        json.dumps({
            "schema_version": 1,
            "entries": [{
                "dataset_id": CASH.name,
                "strategy": "cash-and-carry",
                "entry_market_date": "2026-06-02",
                "fixture_path": CASH.name,
            }],
        }, indent=2)
        + "\n"
    )

    candidate_root = tmp_path / "pre-registered-cash"
    shutil.copytree(CASH, candidate_root)
    manifest_path = candidate_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["selection_provenance"] = {
        "schema_version": 1,
        "selection_kind": "pre_registered_sample",
        "strategy": "cash-and-carry",
        "source": {
            "workflow_run": "37487331716",
            "artifact_id": "11423128537",
            "artifact_name": (
                "cash-historical-market-day-sample-37487331716"
            ),
            "artifact_digest": (
                "sha256:"
                "72714c034d8bccfe2f5e705b177f0db0864251dcf3f8ecdd59d66ab9c90e271e"
            ),
        },
        "sampling": {
            "policy_version": "systematic-stratified-sha256-v1",
            "seed": "cash-stage2-baseline-v1",
            "start_date": "2026-06-01",
            "end_date": "2026-06-10",
            "population_size": 10,
            "requested_sample_size": 3,
            "selected_market_dates": [
                "2026-06-02",
                "2026-06-04",
                "2026-06-08",
            ],
            "evidence_sha256": (
                "8a85c5d87b026128da449f4999c0d77d2809472a573b53f5e327cec6998c6549"
            ),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps({
            "schema_version": 1,
            "items": [
                inventory_item(
                    candidate_root,
                    run="37327804191",
                    name="pre-registered-cash-2026-06-02",
                    compact_id="11398999999",
                    parent_id="11353125961",
                    parent_digest=(
                        "1d1ca77522befbc4fa2eb27c57fa15c15eb4915db50cf1fc08beb0c6f8fcfa31"
                    ),
                )
            ],
        })
    )
    output_dir = tmp_path / "planner-report"

    subprocess.run(
        [
            sys.executable,
            "scripts/plan_historical_campaign.py",
            str(inventory_path),
            "--campaign-prefix",
            "pre-registered-test",
            "--fixture-root",
            str(fixture_root),
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    report = json.loads((output_dir / "report.json").read_text())
    assert report["selected_count"] == 0
    assert report["excluded_pinned_count"] == 1
    excluded = report["excluded_pinned"][0]
    assert excluded["entry_market_date"] == "2026-06-02"
    assert excluded["selection_provenance_status"] == "pinned_missing"
    assert excluded["candidate_selection_provenance_sha256"].startswith(
        "sha256:"
    )
    assert excluded["pinned_selection_provenance_sha256"] == "absent"
