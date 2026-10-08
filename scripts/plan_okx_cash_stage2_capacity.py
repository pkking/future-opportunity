from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.backtest.cash_stage2_capacity import (
    CASH_STAGE2_CAPACITY_FAMILY,
    CASH_STAGE2_CAPACITY_MODULE,
    CASH_STAGE2_CAPACITY_SCAN_END,
    CASH_STAGE2_CAPACITY_SCAN_START,
    CASH_STAGE2_TARGET_DAYS,
    plan_cash_stage2_capacity,
)
from future_opportunity.backtest.history_publication_frontier import (
    inclusive_date_chunks,
)


BASE_URL = "https://www.okx.com"
ROOT = Path(__file__).parents[1]
CORPUS_INDEX = ROOT / "tests/fixtures/historical/corpus-index.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--scan-start",
        type=date.fromisoformat,
        default=CASH_STAGE2_CAPACITY_SCAN_START,
    )
    parser.add_argument(
        "--scan-end",
        type=date.fromisoformat,
        default=CASH_STAGE2_CAPACITY_SCAN_END,
    )
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
    return int(
        datetime.combine(value, datetime.min.time(), tzinfo=UTC).timestamp()
        * 1000
    )


def pinned_cash_dates() -> tuple[str, ...]:
    raw = json.loads(CORPUS_INDEX.read_text())
    entries = raw.get("entries")
    if not isinstance(entries, list):
        raise ValueError("historical corpus index requires entries")
    return tuple(
        sorted(
            str(item["entry_market_date"])
            for item in entries
            if isinstance(item, dict)
            and item.get("strategy") == "cash-and-carry"
        )
    )


def inclusive_days(start: date, end: date) -> tuple[str, ...]:
    if end < start:
        raise ValueError("scan_end must not precede scan_start")
    values: list[str] = []
    cursor = start
    while cursor <= end:
        values.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return tuple(values)


def main() -> None:
    args = parse_args()
    scan_dates = inclusive_days(args.scan_start, args.scan_end)
    scan_set = set(scan_dates)
    candidate_counts: dict[str, int | None] = {
        market_date: 0 for market_date in scan_dates
    }
    observations: list[dict[str, Any]] = []

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for chunk_start, chunk_end in inclusive_date_chunks(
            args.scan_start,
            args.scan_end,
        ):
            target_dates = [
                market_date
                for market_date in scan_dates
                if chunk_start
                <= date.fromisoformat(market_date)
                <= chunk_end
            ]
            query = OkxHistoricalCatalogQuery(
                module=CASH_STAGE2_CAPACITY_MODULE,
                instrument_type="FUTURES",
                date_aggregation="daily",
                begin_ms=day_ms(chunk_start),
                end_ms=day_ms(chunk_end),
                instrument_families=(CASH_STAGE2_CAPACITY_FAMILY,),
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
                        if market_date in scan_set:
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

    pinned = pinned_cash_dates()
    capacity = plan_cash_stage2_capacity(
        candidate_counts,
        pinned_dates=pinned,
        target_days=CASH_STAGE2_TARGET_DAYS,
    )
    report = {
        "schema_version": 1,
        "evidence_type": "cash_stage2_source_capacity_plan",
        "observed_at": datetime.now(UTC).isoformat(),
        "source": {
            "endpoint": f"{BASE_URL}{OKX_HISTORY_ENDPOINT}",
            "module": CASH_STAGE2_CAPACITY_MODULE,
            "instrument_type": "FUTURES",
            "instrument_family": CASH_STAGE2_CAPACITY_FAMILY,
            "date_aggregation": "daily",
        },
        "scan": {
            "start": args.scan_start.isoformat(),
            "end": args.scan_end.isoformat(),
            "date_count": len(scan_dates),
        },
        "pinned_cash_dates": list(pinned),
        "candidate_counts": candidate_counts,
        "capacity": capacity,
        "observations": observations,
        "note": (
            "Read-only availability plan. Candidate selection depends only on "
            "source availability and already-pinned dates. It does not acquire "
            "archives, inspect economics, dispatch promotion, or mutate corpus."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(capacity, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
