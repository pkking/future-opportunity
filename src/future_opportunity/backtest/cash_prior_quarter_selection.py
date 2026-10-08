from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Sequence

from future_opportunity.backtest.availability_selection import (
    POLICY_VERSION,
    AvailabilitySelectionRequest,
    replay_availability_selection,
)


SOURCE_RUN = "37754484440"
SOURCE_ARTIFACT_ID = "11539801691"
SOURCE_DIGEST = "sha256:d1f34518fc4821d4183eb4d009722d6ec7264cc02ac4e5f12172fa16e3ae2da6"
EXPECTED_QUARTERS = (
    ("2025-Q3", "2025-07-01", "2025-09-25", 87, "BTC-USDT-250926",
     "2025-09-25T00:15:00+00:00", "2025-09-26T08:00:00+00:00"),
    ("2025-Q4", "2025-09-27", "2025-12-25", 90, "BTC-USDT-251226",
     "2025-12-25T00:15:00+00:00", "2025-12-26T08:00:00+00:00"),
)


def validate_cash_prior_quarter_preregistration(
    raw: dict[str, Any],
    *,
    pinned_cash_market_dates: Sequence[str],
) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version", "evidence_type", "strategy",
        "selection_policy_version", "source_capacity_evidence",
        "quarters", "invariants",
    }:
        raise ValueError("Cash cohort pre-registration schema mismatch")
    if raw["schema_version"] != 1 or raw["evidence_type"] != (
        "cash_quarter_cohort_pre_registered_availability_selection"
    ):
        raise ValueError("unsupported Cash cohort pre-registration schema")
    if raw["strategy"] != "cash-and-carry" or raw["selection_policy_version"] != POLICY_VERSION:
        raise ValueError("unexpected strategy or selection policy")

    source = raw["source_capacity_evidence"]
    if not isinstance(source, dict) or source != {
        "workflow_run": SOURCE_RUN,
        "artifact_name": "cash-2025-q3-q4-source-capacity",
        "artifact_id": SOURCE_ARTIFACT_ID,
        "artifact_digest": SOURCE_DIGEST,
        "source_module": "4",
        "instrument_type": "FUTURES",
        "instrument_family": "BTC-USDT",
        "daily_catalog_date_aggregation": "daily",
    }:
        raise ValueError("frozen Cash source capacity evidence mismatch")
    if raw["invariants"] != {
        "date_selection_before_outcome_evaluation": True,
        "no_outcome_based_replacement": True,
        "frozen_selected_date_count": 24,
        "economic_assessment_not_performed": True,
        "source_catalog_is_not_complete_l2_evidence": True,
        "automatic_acquisition": False,
        "automatic_promotion": False,
    }:
        raise ValueError("Cash pre-registration governance invariants mismatch")

    quarters = raw["quarters"]
    if not isinstance(quarters, list) or len(quarters) != 2:
        raise ValueError("Cash pre-registration requires exactly two quarters")

    all_dates: list[str] = []
    replay_evidence: list[dict[str, Any]] = []
    pinned = set(pinned_cash_market_dates)
    if len(pinned) != len(pinned_cash_market_dates):
        raise ValueError("current pinned Cash market dates must be unique")

    for item, expected in zip(quarters, EXPECTED_QUARTERS, strict=True):
        if not isinstance(item, dict) or set(item) != {
            "quarter", "start_date", "end_date", "population_size",
            "requested_sample_size", "excluded_market_dates",
            "selected_market_dates", "future_id",
            "entry_time_utc", "exit_at", "expiry_at",
        }:
            raise ValueError("quarter selection fields differ from schema")
        quarter, start, end, population, future, exit_at, expiry_at = expected
        if (
            item["quarter"] != quarter or item["start_date"] != start
            or item["end_date"] != end or item["population_size"] != population
            or item["future_id"] != future
            or item["exit_at"] != exit_at or item["expiry_at"] != expiry_at
            or item["entry_time_utc"] != "00:15:00"
            or item["requested_sample_size"] != 12
            or item["excluded_market_dates"] != []
        ):
            raise ValueError("quarter selection differs from frozen design")
        request = AvailabilitySelectionRequest(
            strategy="cash-and-carry", start_date=start, end_date=end,
            sample_size=12, excluded_market_dates=(),
        )
        replay = replay_availability_selection(request)
        if (
            replay.population_size != item["population_size"]
            or list(replay.selected_market_dates) != item["selected_market_dates"]
        ):
            raise ValueError("Cash quarter selected dates differ from deterministic replay")

        horizon_exit = datetime.fromisoformat(exit_at).astimezone(UTC)
        horizon_expiry = datetime.fromisoformat(expiry_at).astimezone(UTC)
        for day in replay.selected_market_dates:
            entry = datetime.fromisoformat(day + "T00:15:00+00:00")
            if not entry < horizon_exit < horizon_expiry:
                raise ValueError("Cash entry/exit/expiry timestamp ordering violated")
            if day in pinned:
                raise ValueError("quarter selection overlaps pinned Cash market day")
        all_dates.extend(replay.selected_market_dates)
        replay_evidence.append({
            "quarter": quarter,
            "requested_sample_size": 12,
            "population_size": replay.population_size,
            "selected_market_dates": list(replay.selected_market_dates),
            "selection_evidence_sha256": replay.evidence_sha256,
        })

    if len(all_dates) != 24 or len(set(all_dates)) != 24:
        raise ValueError("Cash selected days must be exactly 24 unique dates")

    return {
        "schema_version": 1,
        "evidence_type": "cash_prior_quarter_pre_registration_control",
        "source_capacity_evidence": source,
        "selection_policy_version": POLICY_VERSION,
        "selected_market_date_count": 24,
        "quarters": replay_evidence,
        "selected_market_dates": sorted(all_dates),
        "acquisition_approved": False,
        "promotion_approved": False,
        "economics_inspected_for_selection": False,
        "note": (
            "Exact research dates frozen before return assessment. "
            "No substitution after outcomes; selection control does not "
            "verify 00:15 orderbooks or authorize acquisition or promotion."
        ),
    }
