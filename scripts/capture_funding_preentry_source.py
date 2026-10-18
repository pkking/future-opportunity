"""Manual-only prospectively timed OKX public Funding evidence capture."""
from __future__ import annotations

import argparse
import json
import traceback
from datetime import UTC, datetime, time
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.backtest.funding_asof_capture import validate_preentry_source
from future_opportunity.backtest.funding_raw_feature_lineage import (
    FUNDING_ENDPOINT,
    SPOT_ENDPOINT,
)

BASE_URL = "https://www.okx.com"
FUNDING_QUERY = {"instId": "BTC-USDT-SWAP", "limit": "400"}
SPOT_QUERY = {"instId": "BTC-USDT", "bar": "1Dutc", "limit": "100"}


def _now() -> datetime:
    return datetime.now(UTC)


def _public_source(client: httpx.Client, endpoint: str, query: dict[str, str]) -> dict[str, Any]:
    # No exchange credentials, write routes, pagination fallback, or retries.
    response = client.get(BASE_URL + endpoint, params=query)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("code") != "0":
        raise ValueError("official public source did not succeed")
    if not isinstance(payload.get("data"), list):
        raise ValueError("official public source must return list data")
    return payload


def capture_today(output: Path) -> dict[str, Any]:
    """Make at most two GET requests; fail before any network outside UTC window."""
    begun = _now()
    midnight = datetime.combine(begun.date(), time.min, tzinfo=UTC)
    entry = midnight.replace(minute=15)
    if not midnight <= begun < entry:
        raise ValueError("preentry source capture must start at UTC 00:00..00:15")
    timing: dict[str, str] = {"entry_at": entry.isoformat()}
    # No source call is allowed after entry. We explicitly check after each GET.
    with httpx.Client(timeout=5, follow_redirects=False) as client:
        timing["funding_request_started_at"] = _now().isoformat()
        if _now() >= entry:
            raise ValueError("expired UTC entry before funding request")
        funding = _public_source(client, FUNDING_ENDPOINT, FUNDING_QUERY)
        received = _now()
        timing["funding_response_received_at"] = received.isoformat()
        if received >= entry:
            raise ValueError("funding response received after entry")
        timing["spot_request_started_at"] = _now().isoformat()
        if _now() >= entry:
            raise ValueError("expired UTC entry before spot request")
        spot = _public_source(client, SPOT_ENDPOINT, SPOT_QUERY)
        received = _now()
        timing["spot_response_received_at"] = received.isoformat()
        if received >= entry:
            raise ValueError("spot response received after entry")
    captured = _now()
    if captured >= entry:
        raise ValueError("capture completed after 00:15 UTC; do not publish as-of")
    raw = {
        "schema_version": 1,
        "captured_at": captured.isoformat(),
        "start_date": begun.date().isoformat(),
        "end_date": begun.date().isoformat(),
        "seed": "prospective-observation-only-no-regime-sampling",
        "requested_per_regime": 1,
        "pinned_market_dates": [],
        "funding_query": FUNDING_QUERY,
        "funding_response": funding,
        "spot_query": SPOT_QUERY,
        "spot_response": spot,
    }
    result = validate_preentry_source(raw, timing)
    # Persist only a completely validated capture, never half-sourced evidence.
    output.mkdir(parents=True, exist_ok=True)
    (output / "raw-api-capture.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    (output / "http-timing.json").write_text(json.dumps(timing, indent=2, sort_keys=True) + "\n")
    (output / "preentry-research-evidence.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(capture_today(args.output_dir), indent=2))
    except Exception as exc:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "error.json").write_text(json.dumps({
            "status": "UNASSESSED",
            "error_type": type(exc).__name__,
            "reason": str(exc),
            "detail": traceback.format_exc(),
            "point_in_time_publication_verified": False,
            "acquisition_approved": False,
            "promotion_approved": False,
        }, indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()
