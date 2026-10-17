from __future__ import annotations

import argparse
import json
import time
import traceback
from datetime import UTC, date, datetime
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

WINDOWS_PATH = ROOT / "docs/historical-acquisition-plans/funding-2026-sep-oct-regime-source-windows-v1.json"

def registered_research_window(window_id: str) -> dict[str, Any]:
    registry = json.loads(WINDOWS_PATH.read_text())
    if registry.get("schema_version") != 1 or registry.get("research_only") is not True:
        raise ValueError("invalid Funding source window registry")
    if not (registry.get("outcome_blind") is True
            and registry.get("selection_before_source_inspection") is True
            and registry.get("acquisition_approved") is False
            and registry.get("promotion_approved") is False
            and registry.get("volatility_threshold_bps") == "100"
            and registry.get("request_per_regime") == 2):
        raise ValueError("Funding source window registry governance mismatch")
    windows = registry.get("candidate_windows")
    if not isinstance(windows, list) or len(windows) != 3:
        raise ValueError("Funding research requires three frozen windows")
    seen_days: set[int] = set()
    ids: set[str] = set()
    for window in windows:
        if not isinstance(window, dict) or set(window) != {"id", "start_date", "end_date", "seed"}:
            raise ValueError("unexpected Funding window fields")
        start = date.fromisoformat(window["start_date"])
        end = date.fromisoformat(window["end_date"])
        if (end - start).days != 6 or end > date(2026, 10, 17):
            raise ValueError("Funding window must be seven historical days")
        days = set(range(start.toordinal(), end.toordinal() + 1))
        if window["id"] in ids or seen_days & days:
            raise ValueError("duplicate or overlapping Funding windows")
        if not isinstance(window["seed"], str) or not window["seed"]:
            raise ValueError("Funding research seed must be fixed")
        ids.add(window["id"])
        seen_days.update(days)
    matches = [w for w in windows if w["id"] == window_id]
    if len(matches) != 1:
        raise ValueError("unknown Funding window ID")
    return matches[0]



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
    parser.add_argument("--window-id", default=None)
    args = parser.parse_args()
    fixed = registered_research_window(args.window_id) if args.window_id else None
    if fixed:
        args.start_date, args.end_date = fixed["start_date"], fixed["end_date"]
    seed = fixed["seed"] if fixed else "2026-09-funding-raw-probe-v1"

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
            "seed": seed,
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
        coverage = {
            "schema_version": 1,
            "evidence_type": "funding_regime_source_coverage",
            "window_id": args.window_id or "legacy",
            "start_date": args.start_date,
            "end_date": args.end_date,
            "seed": seed,
            "source_sha256": reconstructed["source_sha256"],
            "source_authentication_status": reconstructed["source_authentication_status"],
            "point_in_time_publication_verified": False,
            "regimes": research["regimes"],
            "missing_days": reconstructed["missing_days"],
            "quota_fully_met": research["quota_fully_met"],
            "acquisition_approved": False,
            "promotion_approved": False,
        }
        (output / "coverage-summary.json").write_text(
            json.dumps(coverage, indent=2, sort_keys=True) + "\n"
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
