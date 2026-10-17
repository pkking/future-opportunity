from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT, OkxHistoricalCatalogQuery, parse_okx_history_catalog,
)

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "docs/historical-acquisition-plans/cash-2025q2-source-capacity-study-v1.json"
ENDPOINT = "https://www.okx.com" + OKX_HISTORY_ENDPOINT


def frozen_daily_population(raw: dict[str, Any]) -> tuple[str, ...]:
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version", "evidence_type", "study_id", "research_only",
        "outcome_blind", "source_catalog_module", "source_catalog_date_aggregation",
        "strategy", "instrument_family", "spot_instrument", "future_id",
        "expiry_at", "study_start_date", "study_end_date",
        "pre_expiry_exit_at", "target_sample_size", "proposed_sampling_policy",
        "candidate_selection_prohibited_until_source_verification",
        "known_independent_l2_source_probe_run",
        "known_independent_l2_source_probe_artifact_id",
        "known_probe_date", "source_calendar_availability",
        "economic_outcomes_inspected", "acquisition_approved", "promotion_approved",
    }:
        raise ValueError("Cash source capacity research registry schema mismatch")
    if not (
        raw["schema_version"] == 1
        and raw["research_only"] is True
        and raw["outcome_blind"] is True
        and raw["economic_outcomes_inspected"] is False
        and raw["acquisition_approved"] is False
        and raw["promotion_approved"] is False
        and raw["candidate_selection_prohibited_until_source_verification"] is True
        and raw["source_calendar_availability"] == "unverified"
        and raw["source_catalog_module"] == "4"
        and raw["source_catalog_date_aggregation"] == "daily"
        and raw["future_id"] == "BTC-USDT-250627"
        and raw["instrument_family"] == raw["spot_instrument"] == "BTC-USDT"
        and raw["target_sample_size"] == 12
        and raw["proposed_sampling_policy"] == "availability-even-rank-v1"
    ):
        raise ValueError("Cash study scope or governance mismatch")
    start, end = date.fromisoformat(raw["study_start_date"]), date.fromisoformat(raw["study_end_date"])
    expiry = datetime.fromisoformat(raw["expiry_at"])
    exit_at = datetime.fromisoformat(raw["pre_expiry_exit_at"])
    if (
        start.isoformat() != "2025-03-29"
        or end.isoformat() != "2025-06-26"
        or expiry.tzinfo is None or exit_at.tzinfo is None
        or expiry.astimezone(UTC).isoformat() != "2025-06-27T08:00:00+00:00"
        or exit_at.astimezone(UTC).isoformat() != "2025-06-26T00:15:00+00:00"
    ):
        raise ValueError("frozen Q2 source population/date/expiry mismatch")
    if (end - start).days != 89:
        raise ValueError("Cash 2025Q2 source study requires exactly 90 calendar days")
    return tuple((start + timedelta(days=i)).isoformat() for i in range(90))


def catalog_query(day: str, kind: str) -> OkxHistoricalCatalogQuery:
    value = int(datetime.combine(
        date.fromisoformat(day), datetime.min.time(), tzinfo=UTC
    ).timestamp() * 1000)
    if kind == "SPOT":
        return OkxHistoricalCatalogQuery(
            module="4", instrument_type="SPOT", date_aggregation="daily",
            begin_ms=value, end_ms=value, instrument_ids=("BTC-USDT",),
        )
    if kind == "FUTURES":
        return OkxHistoricalCatalogQuery(
            module="4", instrument_type="FUTURES", date_aggregation="daily",
            begin_ms=value, end_ms=value, instrument_families=("BTC-USDT",),
        )
    raise ValueError("unsupported source type")


def classify_catalog_response(
    payload: dict[str, Any], query: OkxHistoricalCatalogQuery,
    day: str,
) -> dict[str, Any]:
    files = parse_okx_history_catalog(payload, query)
    exact = [
        x for x in files
        if x.data_date.date().isoformat() == day
        and (x.instrument_id == "BTC-USDT" if query.instrument_type == "SPOT"
             else x.instrument_family == "BTC-USDT")
    ]
    if len(exact) == 1:
        return {
            "status": "unique_catalog_archive_only", "candidate_count": 1,
            "archive_filename": exact[0].filename,
            "contract_member_inside_futures_archive_verified": False,
            "sampled_book_verified": False,
        }
    return {
        "status": "missing" if not exact else "ambiguous",
        "candidate_count": len(exact),
        "contract_member_inside_futures_archive_verified": False,
        "sampled_book_verified": False,
    }


def get_response(
    client: httpx.Client, query: OkxHistoricalCatalogQuery,
) -> dict[str, Any]:
    for attempt in range(4):
        response = client.get(ENDPOINT, params=query.params())
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(0.5 * (attempt + 1))
            continue
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("code") != "0":
            raise ValueError("official OKX historical catalog rejected source request")
        return payload
    raise RuntimeError("official historical catalog retries exhausted")


def scan_population(
    client: httpx.Client, days: tuple[str, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    observations = []
    raw_bodies: dict[str, Any] = {}
    for day in days:
        results = {}
        for kind in ("FUTURES", "SPOT"):
            query = catalog_query(day, kind)
            key = day + "/" + kind
            try:
                raw = get_response(client, query)
                encoded = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
                digest = hashlib.sha256(encoded).hexdigest()
                raw_bodies[key] = {"query": query.params(), "response": raw, "sha256": digest}
                results[kind.lower()] = {
                    **classify_catalog_response(raw, query, day), "response_sha256": digest,
                }
            except (httpx.HTTPError, RuntimeError, ValueError, KeyError, TypeError) as error:
                results[kind.lower()] = {
                    "status": "error", "reason": type(error).__name__,
                    "sampled_book_verified": False,
                }
            time.sleep(0.2)
        observations.append({"market_date": day, **results})
    return observations, raw_bodies


def summary_for(
    registered_days: tuple[str, ...], observations: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(observations) != len(registered_days) or [
        x["market_date"] for x in observations
    ] != list(registered_days):
        raise ValueError("source scan must account for all frozen dates in order")
    paired = [
        x["market_date"] for x in observations
        if x["futures"]["status"] == "unique_catalog_archive_only"
        and x["spot"]["status"] == "unique_catalog_archive_only"
    ]
    errors = [
        x["market_date"] for x in observations
        if x["futures"]["status"] == "error" or x["spot"]["status"] == "error"
    ]
    return {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_retrospective_daily_catalog_population",
        "requested_calendar_days": len(registered_days),
        "source_catalog_days": len(observations),
        "paired_catalog_day_count": len(paired),
        "paired_catalog_dates": paired,
        "query_error_days": errors,
        "source_population_complete": len(errors) == 0,
        "futures_member_identified_per_candidate_day": False,
        "l2_sampled_per_candidate_day": False,
        "historical_selection_frozen": False,
        "sampled_economic_returns_inspected": False,
        "research_only": True,
        "acquisition_approved": False,
        "promotion_approved": False,
        "observations": observations,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    days = frozen_daily_population(json.loads(REGISTRY.read_text()))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=45, follow_redirects=True) as client:
        observations, raw = scan_population(client, days)
    report = summary_for(days, observations)
    (args.output_dir / "catalog-raw-api-capture.json").write_text(
        json.dumps(raw, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "source-calendar-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "paired_catalog_day_count": report["paired_catalog_day_count"],
        "query_error_days": len(report["query_error_days"]),
        "futures_member_identified_per_candidate_day": False,
        "acquisition_approved": False,
    }))


if __name__ == "__main__":
    main()
