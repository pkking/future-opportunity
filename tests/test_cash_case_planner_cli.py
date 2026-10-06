from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


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
