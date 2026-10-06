from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from future_opportunity.backtest.acquisition import (
    parse_historical_acquisition_manifest,
)


def test_acquisition_composer_cli_emits_dispatch_ready_json(
    tmp_path: Path,
) -> None:
    cash_plan = tmp_path / "cash-plan.json"
    cash_plan.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "evidence_type": "read_only_cash_acquisition_case_plan",
                "template": {
                    "future_id": "BTC-USDT-260626",
                    "expiry_at": "2026-06-26T08:00:00+00:00",
                    "exit_at": "2026-06-25T00:15:00+00:00",
                    "entry_time_utc": "00:15:00",
                },
                "selected_count": 1,
                "excluded_count": 0,
                "cash_cases": [
                    {
                        "entry_at": "2026-06-03T00:15:00+00:00",
                        "entry_market_date": "2026-06-03",
                        "exit_at": "2026-06-25T00:15:00+00:00",
                        "expiry_at": "2026-06-26T08:00:00+00:00",
                        "future_id": "BTC-USDT-260626",
                    }
                ],
                "excluded": [],
                "source_reports": ["000/report.json"],
                "note": "read-only",
            }
        )
        + "\n"
    )
    output = tmp_path / "acquisition.json"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/compose_historical_acquisition.py",
            "--acquisition-id",
            "composed-wave",
            "--planner-campaign-prefix",
            "composed-review",
            "--funding-start-date",
            "2026-09-04",
            "--funding-end-date",
            "2026-09-05",
            "--cash-case-plan",
            str(cash_plan),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text())
    assert payload == json.loads(completed.stdout)
    parsed = parse_historical_acquisition_manifest(payload)
    assert parsed.total_items == 3
    assert parsed.funding is not None
    assert parsed.funding.market_dates == (
        "2026-09-04",
        "2026-09-05",
    )
    assert parsed.cash_cases[0].entry_market_date == "2026-06-03"
