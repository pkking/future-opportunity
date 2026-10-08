from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


POLICY_VERSION = "pre-entry-funding-regime-research-v1"
REGIMES = (
    "negative_low_volatility",
    "negative_high_volatility",
    "nonnegative_low_volatility",
    "nonnegative_high_volatility",
)
VOLATILITY_THRESHOLD_BPS = Decimal("100")
INPUT_KEYS = {
    "schema_version", "evidence_type", "policy_version", "seed",
    "start_date", "end_date", "requested_per_regime",
    "source", "pinned_market_dates", "missing_market_dates", "observations",
}
ROW_KEYS = {
    "market_date", "entry_at", "features_observed_at",
    "funding_observed_at", "volatility_window_end_at",
    "lagged_funding_rate", "trailing_spot_volatility_bps",
    "source_record_id", "source_record_sha256",
}
SOURCE_KEYS = {"provider", "instrument_id", "artifact_digest", "observation_contract"}


def _sha256(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("source digest must be text")
    value = value.removeprefix("sha256:")
    if len(value) != 64:
        raise ValueError("source digest must be SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("source digest must be hex SHA-256") from error
    return value.lower()


def _moment(raw: str, field: str) -> datetime:
    if not isinstance(raw, str):
        raise ValueError(f"{field} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as error:
        raise ValueError(f"{field} invalid ISO timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(UTC)


def _decimal(raw: Any, field: str) -> Decimal:
    if not isinstance(raw, str):
        raise ValueError(f"{field} must be a decimal string")
    try:
        value = Decimal(raw)
    except InvalidOperation as error:
        raise ValueError(f"{field} must be a decimal") from error
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    return value


def _chronological_dates(items: Any, field: str) -> tuple[str, ...]:
    if not isinstance(items, list) or not all(isinstance(v, str) for v in items):
        raise ValueError(f"{field} must be a list of dates")
    for item in items:
        date.fromisoformat(item)
    if items != sorted(set(items)):
        raise ValueError(f"{field} must be sorted and unique")
    return tuple(items)


def plan_funding_regime_research(raw: dict[str, Any]) -> dict[str, Any]:
    """Retrospective ex-ante *research* planning only; not promotion provenance.

    The caller must separately authenticate feature origins. Neither strategy
    outcomes nor realized returns are legal selection inputs.
    """
    if not isinstance(raw, dict) or set(raw) != INPUT_KEYS:
        raise ValueError("funding regime input fields differ from exact schema")
    if raw["schema_version"] != 1 or raw["evidence_type"] != "funding_pre_entry_regime_features":
        raise ValueError("unsupported funding regime input schema")
    if raw["policy_version"] != POLICY_VERSION:
        raise ValueError("unsupported funding regime research policy")
    if not isinstance(raw["seed"], str) or not raw["seed"]:
        raise ValueError("regime selection requires an explicit fixed seed")
    count = raw["requested_per_regime"]
    if type(count) is not int or count <= 0:
        raise ValueError("requested_per_regime must be a positive integer")

    start, end = date.fromisoformat(raw["start_date"]), date.fromisoformat(raw["end_date"])
    if end < start:
        raise ValueError("study window is reversed")
    span = (end - start).days + 1
    if span > 366:
        raise ValueError("regime research window must be at most 366 days")
    all_days = tuple(
        (start + timedelta(days=i)).isoformat() for i in range(span)
    )
    pinned = _chronological_dates(raw["pinned_market_dates"], "pinned_market_dates")
    missing = _chronological_dates(raw["missing_market_dates"], "missing_market_dates")
    if not set(pinned).issubset(all_days) or not set(missing).issubset(all_days):
        raise ValueError("pinned/missing dates must be within study window")
    if set(pinned) & set(missing):
        raise ValueError("pinned and missing dates overlap")

    source = raw["source"]
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        raise ValueError("source identity fields differ from exact schema")
    if source["provider"] != "OKX" or source["instrument_id"] != "BTC-USDT-SWAP":
        raise ValueError("unsupported Funding feature source")
    if source["observation_contract"] != "pre_entry_observed_not_outcome":
        raise ValueError("source must explicitly use pre-entry feature semantics")
    source_sha = _sha256(source["artifact_digest"])

    rows = raw["observations"]
    if not isinstance(rows, list):
        raise ValueError("observations must be a list")
    observed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise ValueError("Funding regime row fields differ from exact schema")
        day = row["market_date"]
        if not isinstance(day, str) or day not in all_days:
            raise ValueError("observed market date outside study window")
        if day in observed:
            raise ValueError("duplicate funding regime feature date")
        if day in missing:
            raise ValueError("observed Funding features conflict with missing date")
        entry = _moment(row["entry_at"], "entry_at")
        if entry != datetime.fromisoformat(day + "T00:15:00+00:00"):
            raise ValueError("entry_at must be 00:15 UTC on market_date")
        features_at = _moment(row["features_observed_at"], "features_observed_at")
        funding_at = _moment(row["funding_observed_at"], "funding_observed_at")
        volatility_at = _moment(row["volatility_window_end_at"], "volatility_window_end_at")
        if not funding_at <= features_at < entry:
            raise ValueError("Funding features must be observed before entry")
        if not volatility_at <= features_at < entry:
            raise ValueError("volatility feature window must end before entry")
        funding = _decimal(row["lagged_funding_rate"], "lagged_funding_rate")
        volatility = _decimal(
            row["trailing_spot_volatility_bps"],
            "trailing_spot_volatility_bps",
        )
        if volatility < 0:
            raise ValueError("volatility cannot be negative")
        record_id = row["source_record_id"]
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("missing feature source_record_id")
        _sha256(row["source_record_sha256"])
        sign = "negative" if funding < 0 else "nonnegative"
        level = "high_volatility" if volatility >= VOLATILITY_THRESHOLD_BPS else "low_volatility"
        observed[day] = {
            "market_date": day,
            "regime": f"{sign}_{level}",
            "features_observed_at": features_at.isoformat(),
            "source_record_id": record_id,
            "source_record_sha256": row["source_record_sha256"],
        }

    all_set = set(all_days)
    if set(observed) | set(missing) != all_set:
        raise ValueError("every study day must be observed or explicitly missing")
    population = {
        key: sorted(
            (day for day, item in observed.items()
             if item["regime"] == key and day not in pinned)
        )
        for key in REGIMES
    }
    selected: dict[str, list[str]] = {}
    for regime, dates in population.items():
        ranked = sorted(
            dates,
            key=lambda day: (
                hashlib.sha256(
                    "|".join(
                        (POLICY_VERSION, raw["seed"], source_sha, regime, day)
                    ).encode("utf-8")
                ).hexdigest(),
                day,
            ),
        )
        selected[regime] = sorted(ranked[:count])

    evidence = {
        "schema_version": 1,
        "evidence_type": "funding_lagged_regime_research_selection",
        "policy_version": POLICY_VERSION,
        "input_sha256": hashlib.sha256(
            (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
        ).hexdigest(),
        "source_artifact_digest": "sha256:" + source_sha,
        "seed": raw["seed"],
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "volatility_threshold_bps": str(VOLATILITY_THRESHOLD_BPS),
        "requested_per_regime": count,
        "pinned_dates_excluded": list(pinned),
        "missing_dates": list(missing),
        "classified_pre_entry_features": sorted(observed.values(), key=lambda r: r["market_date"]),
        "regimes": [
            {
                "name": regime,
                "eligible_count": len(population[regime]),
                "eligible_dates": population[regime],
                "selected_count": len(selected[regime]),
                "selected_dates": selected[regime],
                "quota_shortfall": max(count - len(selected[regime]), 0),
            }
            for regime in REGIMES
        ],
        "selected_dates": sorted(day for group in selected.values() for day in group),
        "quota_fully_met": all(len(selected[key]) == count for key in REGIMES),
        "selection_uses_qualified_or_return_outcomes": False,
        "source_authentication_status": "requires_independent_review",
        "acquisition_approved": False,
        "promotion_approved": False,
        "market_wide_opportunity_arrival_rate": None,
        "note": (
            "Historical market-regime research candidate set only. Feature "
            "values and availability must be independently authenticated "
            "before an acquisition-provenance bridge. Never infer independent "
            "future performance from retrospective strata."
        ),
    }
    evidence["evidence_sha256"] = hashlib.sha256(
        (json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    return evidence
