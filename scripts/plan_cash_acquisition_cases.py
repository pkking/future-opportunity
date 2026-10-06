from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from future_opportunity.backtest.cash_case_planning import (
    CashAcquisitionTemplate,
    plan_cash_acquisition_cases,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("discovery_root", type=Path)
    parser.add_argument("--future-id", required=True)
    parser.add_argument("--expiry-at", required=True)
    parser.add_argument("--exit-at", required=True)
    parser.add_argument("--entry-time-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-cases", type=int, default=31)
    args = parser.parse_args()

    reports = sorted(args.discovery_root.rglob("report.json"))
    if not reports:
        raise SystemExit("no Cash discovery report.json files found")

    raw_reports = tuple(json.loads(path.read_text()) for path in reports)
    template = CashAcquisitionTemplate(
        future_id=args.future_id,
        expiry_at=args.expiry_at,
        exit_at=args.exit_at,
        entry_time_utc=args.entry_time_utc,
    )
    plan = plan_cash_acquisition_cases(
        raw_reports,
        template=template,
        max_cases=args.max_cases,
    )

    payload = {
        "schema_version": 1,
        "evidence_type": "read_only_cash_acquisition_case_plan",
        "template": asdict(template),
        "selected_count": plan.selected_count,
        "excluded_count": plan.excluded_count,
        "cash_cases": [
            {
                "entry_at": case.entry_at,
                "exit_at": case.exit_at,
                "future_id": case.future_id,
                "expiry_at": case.expiry_at,
                "entry_market_date": case.entry_market_date,
            }
            for case in plan.selected
        ],
        "excluded": [asdict(item) for item in plan.excluded],
        "source_reports": [
            str(path.relative_to(args.discovery_root))
            for path in reports
        ],
        "note": (
            "Read-only case planning only. Holding-period inputs are explicit; "
            "this output does not prepare, promote, or pin any historical day."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))

    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a") as output:
            output.write(f"selected_count={plan.selected_count}\n")
            output.write(f"excluded_count={plan.excluded_count}\n")
            output.write(
                "cash_cases="
                + json.dumps(
                    [
                        {
                            "entry_at": case.entry_at,
                            "exit_at": case.exit_at,
                            "future_id": case.future_id,
                            "expiry_at": case.expiry_at,
                        }
                        for case in plan.selected
                    ],
                    separators=(",", ":"),
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
