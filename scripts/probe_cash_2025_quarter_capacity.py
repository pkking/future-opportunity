from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.backtest.cash_expiry_probe import (
    evaluate_cash_expiry_probe,
)
from future_opportunity.backtest.cash_prior_quarter_readiness import (
    QUARTERS,
    SPOT_CATALOG_DATES,
    paired_source_readiness,
)


ROOT = Path(__file__).parents[1]
BASE_URL = "https://www.okx.com"


def spot_catalog_status(
    client: httpx.Client,
    market_date: str,
) -> dict[str, str | None]:
    day = datetime.fromisoformat(market_date).replace(tzinfo=UTC)
    ms = int(day.timestamp() * 1000)
    query = OkxHistoricalCatalogQuery(
        module="4", instrument_type="SPOT",
        date_aggregation="daily", begin_ms=ms, end_ms=ms,
        instrument_ids=("BTC-USDT",),
    )
    try:
        response = client.get(
            f"{BASE_URL}{OKX_HISTORY_ENDPOINT}", params=query.params()
        )
        response.raise_for_status()
        raw = response.json()
        if raw.get("code") != "0":
            return {
                "status": "error",
                "reason": f"okx_api_code_{raw.get('code')}",
                "filename": None,
            }
        files = parse_okx_history_catalog(raw, query)
        matching = [
            item for item in files
            if item.instrument_id == "BTC-USDT"
            and item.data_date.date().isoformat() == market_date
        ]
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
        return {
            "status": "error",
            "reason": f"source_query_{type(error).__name__}",
            "filename": None,
        }
    return {
        "status": "unique_catalog_source" if len(matching) == 1 else "unavailable",
        "reason": (
            "catalog_metadata_only_not_orderbook_sample"
            if len(matching) == 1 else f"catalog_match_count_{len(matching)}"
        ),
        "filename": matching[0].filename if len(matching) == 1 else None,
    }


def exit_future_status(
    market_date: str,
    future_id: str,
    destination: Path,
) -> dict[str, str | None]:
    raw_path = destination / f"{market_date}-future-exit.json"
    try:
        run = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/discover_okx_cash_history.py"),
                market_date,
                "--max-raw-mb", "512",
                "--output", str(raw_path),
            ],
            capture_output=True, text=True, check=False, timeout=600,
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "exit_discovery_timeout", "raw_sha256": None}
    if run.returncode != 0 or not raw_path.exists():
        (destination / f"{market_date}-future-error.json").write_text(
            json.dumps(
                {
                    "exit_code": run.returncode,
                    "stderr_tail": run.stderr[-2000:],
                },
                indent=2,
            ) + "\n"
        )
        return {
            "status": "error",
            "reason": f"exit_discovery_failed_exit_{run.returncode}",
            "raw_sha256": None,
        }
    try:
        result = evaluate_cash_expiry_probe(
            json.loads(raw_path.read_text()),
            market_date=market_date,
            expected_future_id=future_id,
        )
    except (ValueError, KeyError, TypeError) as error:
        return {
            "status": "error",
            "reason": f"invalid_exit_discovery_{type(error).__name__}",
            "raw_sha256": None,
        }
    return {
        "status": result.status,
        "reason": result.reason,
        "raw_sha256": result.raw_archive_sha256,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capacity-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = json.loads(args.capacity_report.read_text())
    if (
        raw.get("source", {}).get("module") != "4"
        or raw.get("source", {}).get("instrument_type") != "FUTURES"
        or raw.get("source", {}).get("instrument_family") != "BTC-USDT"
        or raw.get("scan") != {
            "start": "2025-07-01", "end": "2025-12-25",
            "date_count": 178,
        }
    ):
        raise ValueError("capacity source must be exact 2025 Q3/Q4 module-4 scan")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        spots = {}
        for market_date in SPOT_CATALOG_DATES:
            spots[market_date] = spot_catalog_status(client, market_date)
            time.sleep(0.3)

    exits = {}
    for spec in QUARTERS.values():
        market_date = spec["exit_market_date"]
        exits[market_date] = exit_future_status(
            market_date, spec["future_id"], args.output.parent,
        )
    summary = paired_source_readiness(
        raw["candidate_counts"], spot_catalog=spots, futures_exit=exits,
    )
    summary["observed_at"] = datetime.now(UTC).isoformat()
    summary["capacity_source_file"] = str(args.capacity_report)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "quarter_counts": {
            key: val["unique_archive_day_count"]
            for key, val in summary["quarters"].items()
        },
        "spot_fixed_dates_catalog_ready": summary["spot_fixed_dates_catalog_ready"],
        "future_exit_archive_identity_ready": summary["future_exit_archive_identity_ready"],
        "acquisition_ready": summary["acquisition_ready"],
    }, indent=2))


if __name__ == "__main__":
    main()
