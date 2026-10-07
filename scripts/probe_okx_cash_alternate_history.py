from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.backtest.cash_alternate_history import (
    CASH_ALTERNATE_HISTORY_DATES,
    CASH_APPROVED_FUTURE_ID,
    CASH_ENTRY_TIME_UTC,
    CASH_SPOT_ID,
    summarize_alternate_history_coverage,
    trade_retention_eligible,
)


BASE_URL = "https://www.okx.com"
CANDLES_PATH = "/api/v5/market/history-candles"
TRADES_PATH = "/api/v5/market/history-trades"
CATALOG_PATH = "/api/v5/public/market-data-history"
UNMAPPED_CATALOG_MODULES = ("1", "2", "5", "11")
WINDOW = timedelta(minutes=5)
EXPIRED_CONTROL_ID = "BTC-USDT-260626"
EXPIRED_CONTROL_DATE = "2026-06-01"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def request_json(
    client: httpx.Client,
    path: str,
    params: dict[str, str],
) -> tuple[int, dict[str, Any]]:
    for attempt in range(5):
        response = client.get(f"{BASE_URL}{path}", params=params)
        if response.status_code == 429:
            time.sleep(0.5 * (attempt + 1))
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
                "msg": "unexpected non-object OKX response payload",
                "data": [],
            }
        return response.status_code, payload
    raise RuntimeError("OKX rate limit persisted after retries")


def entry_at(market_date: str) -> datetime:
    return datetime.fromisoformat(
        f"{market_date}T{CASH_ENTRY_TIME_UTC}+00:00"
    ).astimezone(UTC)


def timestamp_stats(
    timestamps: list[int],
    *,
    target: datetime,
) -> dict[str, Any]:
    start_ms = int(target.timestamp() * 1000)
    end_ms = int((target + WINDOW).timestamp() * 1000)
    return {
        "returned_count": len(timestamps),
        "min_ts": min(timestamps) if timestamps else None,
        "max_ts": max(timestamps) if timestamps else None,
        "target_window_start": start_ms,
        "target_window_end_exclusive": end_ms,
        "target_window_count": sum(
            1 for value in timestamps if start_ms <= value < end_ms
        ),
    }


def probe_candles(
    client: httpx.Client,
    *,
    market_date: str,
    instrument_id: str,
    instrument_role: str,
) -> dict[str, Any]:
    target = entry_at(market_date)
    params = {
        "instId": instrument_id,
        "bar": "1m",
        "after": str(int((target + WINDOW).timestamp() * 1000)),
        "limit": "20",
    }
    http_status, payload = request_json(client, CANDLES_PATH, params)
    raw = payload.get("data", [])
    rows = raw if isinstance(raw, list) else []
    timestamps: list[int] = []
    for row in rows:
        if isinstance(row, list) and row:
            try:
                timestamps.append(int(str(row[0])))
            except ValueError:
                continue
    return {
        "source": "candles",
        "instrument_role": instrument_role,
        "instrument_id": instrument_id,
        "market_date": market_date,
        "endpoint": f"{BASE_URL}{CANDLES_PATH}",
        "query": params,
        "http_status": http_status,
        "okx_code": str(payload.get("code", "")),
        "okx_message": str(payload.get("msg", "")),
        **timestamp_stats(timestamps, target=target),
    }


def probe_trades(
    client: httpx.Client,
    *,
    market_date: str,
    instrument_id: str,
    instrument_role: str,
    probe_date: date,
) -> dict[str, Any]:
    eligible = trade_retention_eligible(
        market_date,
        probe_date=probe_date,
    )
    target = entry_at(market_date)
    base = {
        "source": "trades",
        "instrument_role": instrument_role,
        "instrument_id": instrument_id,
        "market_date": market_date,
        "endpoint": f"{BASE_URL}{TRADES_PATH}",
        "retention_eligible": eligible,
        "documented_retention": "last_3_calendar_months",
    }
    if not eligible:
        return {
            **base,
            "query": None,
            "http_status": None,
            "okx_code": "not_queried",
            "okx_message": "outside documented public history-trades retention",
            **timestamp_stats([], target=target),
        }

    params = {
        "instId": instrument_id,
        "type": "2",
        "after": str(int((target + WINDOW).timestamp() * 1000)),
        "limit": "100",
    }
    http_status, payload = request_json(client, TRADES_PATH, params)
    raw = payload.get("data", [])
    rows = raw if isinstance(raw, list) else []
    timestamps: list[int] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            timestamps.append(int(str(row.get("ts", ""))))
        except ValueError:
            continue
    return {
        **base,
        "query": params,
        "http_status": http_status,
        "okx_code": str(payload.get("code", "")),
        "okx_message": str(payload.get("msg", "")),
        **timestamp_stats(timestamps, target=target),
    }


def catalog_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    raw_data = payload.get("data", [])
    groups = raw_data if isinstance(raw_data, list) else []
    for group in groups:
        if not isinstance(group, dict):
            continue
        details = group.get("details", [])
        if not isinstance(details, list):
            continue
        for detail in details:
            if not isinstance(detail, dict):
                continue
            files = detail.get("groupDetails", [])
            if not isinstance(files, list):
                continue
            for item in files:
                if not isinstance(item, dict):
                    continue
                candidates.append(
                    {
                        "instId": str(detail.get("instId", "")),
                        "instFamily": str(detail.get("instFamily", "")),
                        "instType": str(detail.get("instType", "")),
                        "dateRangeStart": detail.get("dateRangeStart"),
                        "dateRangeEnd": detail.get("dateRangeEnd"),
                        "filename": str(item.get("filename", "")),
                        "sizeMB": item.get("sizeMB"),
                        "dataTs": item.get("dataTs", item.get("dateTs")),
                    }
                )
    return candidates


def probe_bulk_catalog_inventory(
    client: httpx.Client,
) -> dict[str, Any]:
    dates = ("2026-06-01",) + CASH_ALTERNATE_HISTORY_DATES
    observations: list[dict[str, Any]] = []
    for module in UNMAPPED_CATALOG_MODULES:
        for market_date in dates:
            day = datetime.fromisoformat(market_date).replace(tzinfo=UTC)
            day_ms = int(day.timestamp() * 1000)
            params = {
                "module": module,
                "instType": "FUTURES",
                "instFamilyList": "BTC-USDT",
                "dateAggrType": "daily",
                "begin": str(day_ms),
                "end": str(day_ms),
            }
            http_status, payload = request_json(client, CATALOG_PATH, params)
            candidates = catalog_candidates(payload)
            observations.append(
                {
                    "module": module,
                    "market_date": market_date,
                    "cohort": (
                        "positive_control"
                        if market_date == "2026-06-01"
                        else "pre_registered"
                    ),
                    "endpoint": f"{BASE_URL}{CATALOG_PATH}",
                    "query": params,
                    "http_status": http_status,
                    "okx_code": str(payload.get("code", "")),
                    "okx_message": str(payload.get("msg", "")),
                    "candidate_count": len(candidates),
                    "candidates": candidates,
                }
            )
            time.sleep(0.45)

    summary: dict[str, Any] = {}
    for module in UNMAPPED_CATALOG_MODULES:
        selected = [
            item for item in observations if item["module"] == module
        ]
        positive = selected[0]
        wave = selected[1:]
        filenames = sorted(
            {
                candidate["filename"]
                for item in selected
                for candidate in item["candidates"]
                if candidate["filename"]
            }
        )
        summary[module] = {
            "positive_control_candidate_count": positive["candidate_count"],
            "pre_registered_dates_with_candidates": sum(
                1 for item in wave if item["candidate_count"] > 0
            ),
            "pre_registered_date_count": len(wave),
            "okx_error_dates": sum(
                1 for item in wave if item["okx_code"] != "0"
            ),
            "sample_filenames": filenames[:12],
        }
    return {
        "modules": list(UNMAPPED_CATALOG_MODULES),
        "note": (
            "Module semantics are intentionally not assigned here. "
            "Returned filenames and metadata are captured as discovery evidence."
        ),
        "observations": observations,
        "summary": summary,
    }


def main() -> None:
    args = parse_args()
    started_at = datetime.now(UTC)
    probe_date = started_at.date()
    observations: list[dict[str, Any]] = []

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for market_date in CASH_ALTERNATE_HISTORY_DATES:
            for role, instrument_id in (
                ("future", CASH_APPROVED_FUTURE_ID),
                ("spot", CASH_SPOT_ID),
            ):
                observations.append(
                    probe_candles(
                        client,
                        market_date=market_date,
                        instrument_id=instrument_id,
                        instrument_role=role,
                    )
                )
                time.sleep(0.12)
                observations.append(
                    probe_trades(
                        client,
                        market_date=market_date,
                        instrument_id=instrument_id,
                        instrument_role=role,
                        probe_date=probe_date,
                    )
                )
                time.sleep(0.12)

        controls = [
            probe_candles(
                client,
                market_date=EXPIRED_CONTROL_DATE,
                instrument_id=EXPIRED_CONTROL_ID,
                instrument_role="future",
            ),
            probe_candles(
                client,
                market_date=EXPIRED_CONTROL_DATE,
                instrument_id=CASH_SPOT_ID,
                instrument_role="spot",
            ),
        ]
        bulk_catalog_inventory = probe_bulk_catalog_inventory(client)

    report = {
        "schema_version": 1,
        "evidence_type": "okx_cash_alternate_history_coverage",
        "probe_started_at": started_at.isoformat(),
        "documented_contract": {
            "candles": "historical candlesticks from recent years; 1s limited to 3 months",
            "trades": "public history-trades limited to last 3 months",
        },
        "fixed_inputs": {
            "market_dates": list(CASH_ALTERNATE_HISTORY_DATES),
            "future_id": CASH_APPROVED_FUTURE_ID,
            "spot_id": CASH_SPOT_ID,
            "entry_time_utc": CASH_ENTRY_TIME_UTC,
        },
        "observations": observations,
        "positive_controls": controls,
        "bulk_catalog_inventory": bulk_catalog_inventory,
        "summary": summarize_alternate_history_coverage(observations),
        "note": (
            "Coverage diagnostic only. Target coverage does not authorize "
            "trade/candlestick evidence as equivalent to L2 order-book evidence."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "probe_started_at": report["probe_started_at"],
                "summary": report["summary"],
                "positive_controls": controls,
                "bulk_catalog_summary": bulk_catalog_inventory["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
