"""Strict single-day Funding pre-entry *source observation*, not a trading gate.

Local clock assertions alone do NOT independently authenticate historical
publication; GitHub/Sigstore provenance must be verified separately.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Any

from future_opportunity.backtest.funding_raw_feature_lineage import (
    reconstruct_funding_regime_features,
)
from future_opportunity.backtest.funding_regime_research import (
    plan_funding_regime_research,
)


def _utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} is not an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed.astimezone(UTC)


def validate_preentry_source(
    capture: dict[str, Any], timing: dict[str, Any],
) -> dict[str, Any]:
    """Recompute one future UTC day's observed inputs and fail closed.

    A valid result establishes ONLY internal temporal consistency of a
    collected response. Neither the local clock nor a later-retained artifact
    can certify exchange dissemination time. Never use this as promotion
    authorization.
    """
    required = {
        "entry_at", "funding_request_started_at", "funding_response_received_at",
        "spot_request_started_at", "spot_response_received_at",
    }
    if not isinstance(timing, dict) or set(timing) != required:
        raise ValueError("preentry timing fields differ from schema")
    entry = _utc(timing["entry_at"], "entry_at")
    start_of_day = datetime.combine(entry.date(), time.min, tzinfo=UTC)
    if entry != start_of_day.replace(minute=15):
        raise ValueError("entry must be 00:15 UTC")
    if not isinstance(capture, dict):
        raise ValueError("source capture must be an object")
    if capture.get("start_date") != entry.date().isoformat() or capture.get(
        "end_date"
    ) != entry.date().isoformat():
        raise ValueError("source date must equal observed UTC entry day")
    if capture.get("pinned_market_dates") != []:
        raise ValueError("prospective observation cannot carry pinned selection")
    moments = [_utc(timing[key], key) for key in (
        "funding_request_started_at", "funding_response_received_at",
        "spot_request_started_at", "spot_response_received_at",
    )]
    if not (start_of_day <= moments[0] <= moments[1]
            <= moments[2] <= moments[3] < entry):
        raise ValueError("both source HTTP transactions must finish before entry")
    recorded = _utc(capture.get("captured_at"), "captured_at")
    if not moments[3] <= recorded < entry:
        raise ValueError("captured_at must follow source responses before entry")
    reconstructed = reconstruct_funding_regime_features(capture)
    if (reconstructed["feature_rows_reconstructed"] != 1
        or reconstructed["missing_days"]):
        raise ValueError("missing or stale completed pre-entry source features")
    planner = plan_funding_regime_research(reconstructed["planner_input"])
    obs = reconstructed["planner_input"]["observations"]
    if len(obs) != 1 or obs[0]["entry_at"] != entry.isoformat():
        raise ValueError("reconstructed source date/entry mismatch")
    if planner["selection_uses_qualified_or_return_outcomes"] is not False:
        raise ValueError("preentry sampling must remain outcome-blind")
    if not (planner["acquisition_approved"] is False
            and planner["promotion_approved"] is False):
        raise ValueError("no source observation may authorize promotion")
    return {
        "schema_version": 1,
        "evidence_type": "funding_prospective_preentry_local_http_capture",
        "entry_at": entry.isoformat(),
        "capture_completed_at": recorded.isoformat(),
        "http_transactions_completed_before_entry": True,
        "raw_source_sha256": reconstructed["source_sha256"],
        "source_record_sha256": obs[0]["source_record_sha256"],
        "features_observed_at": obs[0]["features_observed_at"],
        "lagged_funding_rate": obs[0]["lagged_funding_rate"],
        "trailing_spot_volatility_bps": obs[0]["trailing_spot_volatility_bps"],
        "regime": planner["classified_pre_entry_features"][0]["regime"],
        "evidence_status": "local_capture_not_independently_attested",
        "point_in_time_publication_verified": False,
        "exchange_signed": False,
        "source_authentication_status": "requires_independent_provenance_review",
        "acquisition_approved": False,
        "promotion_approved": False,
        "market_wide_opportunity_arrival_rate": None,
        "note": (
            "Original response bytes and local request/receive clock are retained "
            "for review. A separate verified GitHub/Sigstore attestation and "
            "independent timing/source analysis are necessary before any "
            "historical point-in-time evidence claim. No economics or trading."
        ),
    }
