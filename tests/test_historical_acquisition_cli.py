from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_acquisition_cli_emits_normalized_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "acquisition.json"
    output = tmp_path / "resolved.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "acquisition_id": "cli-wave",
                "planner_campaign_prefix": "cli-review",
                "funding": {
                    "start_date": "2026-09-04",
                    "end_date": "2026-09-05",
                },
                "cash_cases": [
                    {
                        "entry_at": "2026-06-04T00:15:00+00:00",
                        "exit_at": "2026-06-25T00:15:00+00:00",
                        "future_id": "BTC-USDT-260626",
                        "expiry_at": "2026-06-26T08:00:00+00:00",
                    }
                ],
            }
        )
        + "\n"
    )

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/resolve_historical_acquisition.py",
            str(manifest),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text())
    assert payload["acquisition_id"] == "cli-wave"
    assert payload["planner_campaign_prefix"] == "cli-review"
    assert payload["funding"]["market_dates"] == [
        "2026-09-04",
        "2026-09-05",
    ]
    assert payload["cash_cases"][0]["entry_market_date"] == "2026-06-04"
    assert payload["total_items"] == 3
    assert json.loads(completed.stdout) == payload
