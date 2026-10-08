from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from future_opportunity.backtest.cash_expiry_probe import (
    CASH_EXPIRY_PROBE_TARGETS,
    CashExpiryProbeResult,
    cash_expiry_probe_summary,
    evaluate_cash_expiry_probe,
)


ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "artifacts/cash-expiry-2025-probe"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    observed: list[CashExpiryProbeResult] = []
    for market_date, future_id in CASH_EXPIRY_PROBE_TARGETS:
        dest = OUTPUT / f"{market_date}-discovery.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/discover_okx_cash_history.py"),
                market_date,
                "--output",
                str(dest),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
        if completed.returncode != 0 or not dest.is_file():
            observed.append(
                CashExpiryProbeResult(
                    market_date,
                    future_id,
                    "error",
                    f"discovery_failed_exit_{completed.returncode}",
                    None,
                )
            )
            (OUTPUT / f"{market_date}-error.json").write_text(
                json.dumps(
                    {
                        "market_date": market_date,
                        "expected_future_id": future_id,
                        "exit_code": completed.returncode,
                        "stderr_tail": completed.stderr[-3000:],
                        "stdout_tail": completed.stdout[-3000:],
                    },
                    indent=2,
                    sort_keys=True,
                ) + "\n"
            )
            continue
        try:
            result = evaluate_cash_expiry_probe(
                json.loads(dest.read_text()),
                market_date=market_date,
                expected_future_id=future_id,
            )
        except (ValueError, TypeError, KeyError) as error:
            result = CashExpiryProbeResult(
                market_date, future_id, "error",
                f"invalid_discovery_evidence_{type(error).__name__}", None,
            )
        observed.append(result)

    summary = cash_expiry_probe_summary(observed)
    summary["observed_at"] = datetime.now(UTC).isoformat()
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
