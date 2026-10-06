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
    parse_historical_selection_provenance,
)


def test_selection_provenance_cli_builds_replayable_evidence(
    tmp_path: Path,
) -> None:
    sample = tmp_path / "sample.json"
    sample.write_text(
        json.dumps(
            historical_sampling_payload(
                sample_historical_market_days(
                    HistoricalSamplingRequest(
                        strategy="funding-carry",
                        start_date="2026-01-01",
                        end_date="2026-01-31",
                        sample_size=5,
                        seed="stage2-baseline-v1",
                    )
                )
            )
        )
        + "\n"
    )
    output = tmp_path / "selection.json"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/build_historical_selection_provenance.py",
            str(sample),
            "--source-workflow-run",
            "37482498880",
            "--artifact-name",
            "historical-market-day-sample-37482498880",
            "--artifact-id",
            "11421537670",
            "--artifact-digest",
            (
                "sha256:bdaab43d0be70a2fc8b43059d39f5341"
                "a2405bf9a0aff00306b90e92e24b8fa2"
            ),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text())
    assert payload == json.loads(completed.stdout)
    parsed = parse_historical_selection_provenance(payload)
    assert parsed.strategy == "funding-carry"
    assert parsed.source.artifact_id == "11421537670"
    assert parsed.selected_market_dates == (
        "2026-01-01",
        "2026-01-08",
        "2026-01-13",
        "2026-01-22",
        "2026-01-29",
    )
