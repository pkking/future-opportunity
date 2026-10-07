from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.backtest.cash_source_readiness import (
    CASH_SOURCE_READINESS_DATES,
    CASH_SOURCE_READINESS_FAMILY,
    CASH_SOURCE_READINESS_MODULE,
    summarize_cash_source_readiness,
)
from future_opportunity.backtest.history_publication_frontier import (
    inclusive_date_chunks,
)


BASE_URL = "https://www.okx.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def get_json(
    client: httpx.Client,
    query: OkxHistoricalCatalogQuery,
) -> tuple[int, dict[str, Any]]:
    for attempt in range(5):
        response = client.get(
            f"{BASE_URL}{OKX_HISTORY_ENDPOINT}",
            params=query.params(),
        )
        if response.status_code == 429:
            time.sleep(0.75 * (attempt + 1))
            continue
        try:
            payload = response.json()
        except ValueError:
            payload = {
                "code": f"http_{response.status_code}",
                "msg": response.text[:500],
                "data": [],
            }
        if not isinstance(payload, dict):
            payload = {
                "code": f"http_{response.status_code}",
                "msg": "unexpected non-object OKX response",
                "data": [],
            }
        return response.status_code, payload
    raise RuntimeError("OKX rate limit persisted after retries")


def day_ms(value: date) -> int:
    return int(datetime.combine(value, datetime.min.time(), tzinfo=UTC).timestamp() * 1000)


def main() -> None:
    args = parse_args()
    required = tuple(CASH_SOURCE_READINESS_DATES)
    required_set = set(required)
    start = date.fromisoformat(min(required))
    end = date.fromisoformat(max(required))
    candidate_counts: dict[str, int | None] = {
        market_date: 0 for market_date in required
    }
    observations: list[dict[str, Any]] = []

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for chunk_start, chunk_end in inclusive_date_chunks(start, end):
            target_dates = [
                market_date
                for market_date in required
                if chunk_start <= date.fromisoformat(market_date) <= chunk_end
            ]
            query = OkxHistoricalCatalogQuery(
                module=CASH_SOURCE_READINESS_MODULE,
                instrument_type="FUTURES",
                date_aggregation="daily",
                begin_ms=day_ms(chunk_start),
                end_ms=day_ms(chunk_end),
                instrument_families=(CASH_SOURCE_READINESS_FAMILY,),
            )
            http_status, payload = get_json(client, query)
            file_rows: list[dict[str, Any]] = []
            parse_error = None

            if str(payload.get("code", "")) == "0":
                try:
                    files = parse_okx_history_catalog(payload, query)
                    counts: defaultdict[str, int] = defaultdict(int)
                    for item in files:
                        market_date = item.data_date.date().isoformat()
                        file_rows.append(
                            {
                                "market_date": market_date,
                                "filename": item.filename,
                                "instrument_family": item.instrument_family,
                                "declared_size_mb": (
                                    str(item.declared_size_mb)
                                    if item.declared_size_mb is not None
                                    else None
                                ),
                                "data_date": item.data_date.isoformat(),
                            }
                        )
                        if market_date in required_set:
                            counts[market_date] += 1
                    for market_date in target_dates:
                        candidate_counts[market_date] = counts[market_date]
                except Exception as error:
                    parse_error = {
                        "type": type(error).__name__,
                        "message": str(error),
                    }
                    for market_date in target_dates:
                        candidate_counts[market_date] = None
            else:
                for market_date in target_dates:
                    candidate_counts[market_date] = None

            observations.append(
                {
                    "chunk_start": chunk_start.isoformat(),
                    "chunk_end": chunk_end.isoformat(),
                    "target_dates": target_dates,
                    "query": query.params(),
                    "source_timezone": query.source_timezone,
                    "http_status": http_status,
                    "okx_code": str(payload.get("code", "")),
                    "okx_message": str(payload.get("msg", "")),
                    "parse_error": parse_error,
                    "files": file_rows,
                }
            )
            time.sleep(0.5)

    readiness = summarize_cash_source_readiness(candidate_counts)
    report = {
        "schema_version": 1,
        "evidence_type": "pre_registered_cash_source_readiness",
        "observed_at": datetime.now(UTC).isoformat(),
        "source": {
            "endpoint": f"{BASE_URL}{OKX_HISTORY_ENDPOINT}",
            "module": CASH_SOURCE_READINESS_MODULE,
            "instrument_type": "FUTURES",
            "instrument_family": CASH_SOURCE_READINESS_FAMILY,
            "date_aggregation": "daily",
        },
        "required_dates": list(required),
        "candidate_counts": candidate_counts,
        "readiness": readiness,
        "observations": observations,
        "note": (
            "Read-only source readiness evidence. all_ready does not dispatch "
            "acquisition, replace dates, or mutate the historical corpus."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(readiness, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
