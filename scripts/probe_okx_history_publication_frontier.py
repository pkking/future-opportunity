from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, date, datetime, time as clock_time, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.backtest.history_publication_frontier import (
    HISTORY_FRONTIER_END,
    HISTORY_FRONTIER_MODULES,
    HISTORY_FRONTIER_PROBE_DATE,
    HISTORY_FRONTIER_START,
    inclusive_date_chunks,
    summarize_cross_module_frontier,
    summarize_module_frontier,
)


BASE_URL = "https://www.okx.com"
UTC_PLUS_8 = timezone(timedelta(hours=8))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def source_timezone(module: str):
    return UTC if module in {"4", "5", "6"} else UTC_PLUS_8


def day_timestamp(value: date, module: str) -> int:
    moment = datetime.combine(value, clock_time.min, tzinfo=source_timezone(module))
    return int(moment.timestamp() * 1000)


def get_catalog(
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


def main() -> None:
    args = parse_args()
    observations: list[dict[str, Any]] = []
    summaries: list[dict[str, object]] = []

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for module in HISTORY_FRONTIER_MODULES:
            available: set[date] = set()
            for chunk_start, chunk_end in inclusive_date_chunks(
                HISTORY_FRONTIER_START,
                HISTORY_FRONTIER_END,
            ):
                query = OkxHistoricalCatalogQuery(
                    module=module,
                    instrument_type="FUTURES",
                    date_aggregation="daily",
                    begin_ms=day_timestamp(chunk_start, module),
                    end_ms=day_timestamp(chunk_end, module),
                    instrument_families=("BTC-USDT",),
                )
                http_status, payload = get_catalog(client, query)
                files = ()
                parse_error = None
                if str(payload.get("code", "")) == "0":
                    try:
                        files = parse_okx_history_catalog(payload, query)
                    except Exception as error:
                        parse_error = {
                            "type": type(error).__name__,
                            "message": str(error),
                        }

                file_rows = []
                for item in files:
                    market_date = item.data_date.date()
                    if HISTORY_FRONTIER_START <= market_date <= HISTORY_FRONTIER_END:
                        available.add(market_date)
                    file_rows.append(
                        {
                            "market_date": market_date.isoformat(),
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

                observations.append(
                    {
                        "module": module,
                        "chunk_start": chunk_start.isoformat(),
                        "chunk_end": chunk_end.isoformat(),
                        "query": query.params(),
                        "source_timezone": query.source_timezone,
                        "http_status": http_status,
                        "okx_code": str(payload.get("code", "")),
                        "okx_message": str(payload.get("msg", "")),
                        "parse_error": parse_error,
                        "file_count": len(file_rows),
                        "files": file_rows,
                    }
                )
                time.sleep(0.5)

            summaries.append(
                summarize_module_frontier(
                    module=module,
                    available_dates=available,
                )
            )

    report = {
        "schema_version": 1,
        "evidence_type": "okx_history_publication_frontier",
        "probe_date": HISTORY_FRONTIER_PROBE_DATE.isoformat(),
        "scan_start": HISTORY_FRONTIER_START.isoformat(),
        "scan_end": HISTORY_FRONTIER_END.isoformat(),
        "modules": list(HISTORY_FRONTIER_MODULES),
        "max_daily_query_days": 10,
        "instrument_type": "FUTURES",
        "instrument_family": "BTC-USDT",
        "observations": observations,
        "module_summaries": summaries,
        "cross_module_summary": summarize_cross_module_frontier(summaries),
        "note": (
            "Availability is derived only from official catalog file metadata. "
            "This diagnostic does not select or replace any historical study date."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "module_summaries": summaries,
                "cross_module_summary": report["cross_module_summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
