from __future__ import annotations

import argparse
import json
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.backtest.funding_raw_feature_lineage import (
    FUNDING_ENDPOINT,
    SPOT_ENDPOINT,
    reconstruct_funding_regime_features,
)
from future_opportunity.backtest.funding_regime_research import (
    plan_funding_regime_research,
)


ROOT = Path(__file__).parents[1]
CORPUS_INDEX = ROOT / "tests/fixtures/historical/corpus-index.json"
BASE_URL = "https://www.okx.com"


def _get_public_api(
    client: httpx.Client,
    endpoint: str,
    params: dict[str, str],
) -> dict[str, Any]:
    for attempt in range(4):
        response = client.get(BASE_URL + endpoint, params=params)
        if response.status_code == 429:
            time.sleep(1 + attempt)
            continue
        response.raise_for_status()
        raw = response.json()
        if not isinstance(raw, dict) or raw.get("code") != "0":
            raise RuntimeError(
                f"official OKX response failed at {endpoint}: "
                f"code={raw.get('code') if isinstance(raw, dict) else 'non-object'}"
            )
        if not isinstance(raw.get("data"), list):
            raise ValueError("OKX data must be an array")
        return raw
    raise RuntimeError(f"official OKX rate limit at {endpoint}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start-date", default="2026-09-15")
    parser.add_argument("--end-date", default="2026-09-21")
    args = parser.parse_args()

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    raw_index = json.loads(CORPUS_INDEX.read_text())
    pinned = sorted(
        {
            row["entry_market_date"]
            for row in raw_index["entries"]
            if row["strategy"] == "funding-carry"
            and args.start_date <= row["entry_market_date"] <= args.end_date
        }
    )

    # A bounded recent fixed research window, NOT an acquisition manifest.
    funding_query = {"instId": "BTC-USDT-SWAP", "limit": "400"}
    spot_query = {"instId": "BTC-USDT", "bar": "1Dutc", "limit": "100"}

    try:
        with httpx.Client(timeout=45, follow_redirects=True) as client:
            funding_payload = _get_public_api(
                client, FUNDING_ENDPOINT, funding_query
            )
            spot_payload = _get_public_api(
                client, SPOT_ENDPOINT, spot_query
            )
        capture = {
            "schema_version": 1,
            "captured_at": datetime.now(UTC).isoformat(),
            "start_date": args.start_date,
            "end_date": args.end_date,
            "seed": "2026-09-funding-raw-probe-v1",
            "requested_per_regime": 2,
            "pinned_market_dates": pinned,
            "funding_query": funding_query,
            "funding_response": funding_payload,
            "spot_query": spot_query,
            "spot_response": spot_payload,
        }
        (output / "raw-api-capture.json").write_text(
            json.dumps(capture, indent=2, sort_keys=True) + "\n"
        )
        reconstructed = reconstruct_funding_regime_features(capture)
        (output / "reconstructed-features.json").write_text(
            json.dumps(reconstructed, indent=2, sort_keys=True) + "\n"
        )
        (output / "planner-input.json").write_text(
            json.dumps(
                reconstructed["planner_input"], indent=2, sort_keys=True
            ) + "\n"
        )
        research = plan_funding_regime_research(
            reconstructed["planner_input"]
        )
        (output / "research-selection.json").write_text(
            json.dumps(research, indent=2, sort_keys=True) + "\n"
        )
        print(
            json.dumps(
                {
                    "capture_status": reconstructed["status"],
                    "funding_rows_received": reconstructed[
                        "funding_rows_received"
                    ],
                    "spot_daily_candles_received": reconstructed[
                        "spot_daily_candles_received"
                    ],
                    "feature_rows_reconstructed": reconstructed[
                        "feature_rows_reconstructed"
                    ],
                    "missing_date_count": len(reconstructed["missing_days"]),
                    "regime_quotas_met": research["quota_fully_met"],
                    "acquisition_approved": False,
                    "promotion_approved": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
    except Exception as error:
        (output / "error.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "evidence_type": "funding_raw_source_probe_error",
                    "error_type": type(error).__name__,
                    "message": str(error),
                    "traceback": traceback.format_exc(),
                    "acquisition_approved": False,
                    "promotion_approved": False,
                },
                indent=2,
                sort_keys=True,
            ) + "\n"
        )
        raise


if __name__ == "__main__":
    main()
