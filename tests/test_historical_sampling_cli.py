from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_sampling_cli_emits_machine_readable_golden_evidence(
    tmp_path: Path,
) -> None:
    output = tmp_path / "sample.json"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/sample_historical_market_days.py",
            "--strategy",
            "funding-carry",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-01-31",
            "--sample-size",
            "5",
            "--seed",
            "stage2-baseline-v1",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text())
    assert payload == json.loads(completed.stdout)
    assert payload["evidence_type"] == (
        "pre_registered_historical_market_day_sample"
    )
    assert payload["selected_dates"] == [
        "2026-01-01",
        "2026-01-08",
        "2026-01-13",
        "2026-01-22",
        "2026-01-29",
    ]
    assert payload["replacement_policy"] == "none-v1"
