from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from future_opportunity.backtest.sampling import (
    HistoricalSamplingRequest,
    historical_sampling_payload,
    sample_historical_market_days,
)
from future_opportunity.backtest.selection_provenance import (
    historical_selection_provenance_payload,
    selection_provenance_from_sampling_evidence,
)


def test_cash_case_planner_cli_emits_acquisition_ready_cases(
    tmp_path: Path,
) -> None:
    discovery_root = tmp_path / "discovery"
    first = discovery_root / "2026-06-03"
    second = discovery_root / "2026-06-04"
    first.mkdir(parents=True)
    second.mkdir(parents=True)

    (first / "report.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "market_date": "2026-06-03",
                "status": "future_discovered",
                "future": {
                    "instrument_id": "BTC-USDT-260626",
                },
            }
        )
        + "\n"
    )
    (second / "report.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "market_date": "2026-06-04",
                "status": "no_unique_future_chain_archive",
            }
        )
        + "\n"
    )

    output = tmp_path / "plan.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/plan_cash_acquisition_cases.py",
            str(discovery_root),
            "--future-id",
            "BTC-USDT-260626",
            "--expiry-at",
            "2026-06-26T08:00:00+00:00",
            "--exit-at",
            "2026-06-25T00:15:00+00:00",
            "--entry-time-utc",
            "00:15:00",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text())
    assert payload["selected_count"] == 1
    assert payload["excluded_count"] == 1
    assert payload["cash_cases"] == [
        {
            "entry_at": "2026-06-03T00:15:00+00:00",
            "entry_market_date": "2026-06-03",
            "exit_at": "2026-06-25T00:15:00+00:00",
            "expiry_at": "2026-06-26T08:00:00+00:00",
            "future_id": "BTC-USDT-260626",
        }
    ]
    assert payload["excluded"] == [
        {
            "discovered_future_id": None,
            "market_date": "2026-06-04",
            "reason": "no_unique_future_chain_archive",
        }
    ]
    assert json.loads(completed.stdout) == payload


def test_cash_case_planner_cli_preserves_verified_selection_provenance(
    tmp_path: Path,
) -> None:
    discovery_root = tmp_path / "discovery"
    for day in ("2026-06-02", "2026-06-04", "2026-06-08"):
        folder = discovery_root / day
        folder.mkdir(parents=True)
        (folder / "report.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "market_date": day,
                    "status": "future_discovered",
                    "future": {"instrument_id": "BTC-USDT-260626"},
                }
            )
            + "\n"
        )

    sample = historical_sampling_payload(
        sample_historical_market_days(
            HistoricalSamplingRequest(
                strategy="cash-and-carry",
                start_date="2026-06-01",
                end_date="2026-06-10",
                sample_size=3,
                seed="cash-stage2-baseline-v1",
            )
        )
    )
    assert sample["selected_dates"] == [
        "2026-06-02",
        "2026-06-04",
        "2026-06-08",
    ]
    provenance = historical_selection_provenance_payload(
        selection_provenance_from_sampling_evidence(
            sample,
            source_workflow_run="37487331716",
            artifact_name="cash-historical-market-day-sample-37487331716",
            artifact_id="11423128537",
            artifact_digest=(
                "sha256:72714c034d8bccfe2f5e705b177f0db0"
                "864251dcf3f8ecdd59d66ab9c90e271e"
            ),
        )
    )
    provenance_path = tmp_path / "selection.json"
    provenance_path.write_text(json.dumps(provenance) + "\n")
    output = tmp_path / "plan.json"

    subprocess.run(
        [
            sys.executable,
            "scripts/plan_cash_acquisition_cases.py",
            str(discovery_root),
            "--future-id",
            "BTC-USDT-260626",
            "--expiry-at",
            "2026-06-26T08:00:00+00:00",
            "--exit-at",
            "2026-06-25T00:15:00+00:00",
            "--entry-time-utc",
            "00:15:00",
            "--selection-provenance",
            str(provenance_path),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text())
    assert payload["selected_count"] == 3
    assert payload["excluded_count"] == 0
    assert payload["selection_provenance"] == provenance
    assert [
        case["entry_market_date"] for case in payload["cash_cases"]
    ] == ["2026-06-02", "2026-06-04", "2026-06-08"]
