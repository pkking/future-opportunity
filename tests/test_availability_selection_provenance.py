from __future__ import annotations

import copy

import pytest

from future_opportunity.backtest.availability_selection import (
    AvailabilitySelectionRequest,
    replay_availability_selection,
)
from future_opportunity.backtest.distribution_report import (
    _selection_provenance_view,
)
from future_opportunity.backtest.selection_provenance import (
    historical_selection_provenance_payload,
    parse_historical_selection_provenance,
    selection_provenance_from_availability_selection,
)


EXCLUDED = (
    "2026-06-01",
    "2026-06-02",
    "2026-06-03",
    "2026-06-04",
    "2026-06-08",
)
EXPECTED = (
    "2026-01-04",
    "2026-01-11",
    "2026-01-18",
    "2026-01-25",
    "2026-01-31",
    "2026-02-07",
    "2026-02-14",
    "2026-02-21",
    "2026-02-28",
    "2026-03-07",
    "2026-03-14",
    "2026-03-21",
    "2026-03-28",
    "2026-04-03",
    "2026-04-10",
    "2026-04-17",
    "2026-04-24",
    "2026-05-01",
    "2026-05-08",
    "2026-05-15",
    "2026-05-22",
    "2026-05-28",
    "2026-06-09",
    "2026-06-16",
    "2026-06-23",
)


def request() -> AvailabilitySelectionRequest:
    return AvailabilitySelectionRequest(
        strategy="cash-and-carry",
        start_date="2026-01-01",
        end_date="2026-06-26",
        excluded_market_dates=EXCLUDED,
        sample_size=25,
    )


def provenance_payload() -> dict[str, object]:
    provenance = selection_provenance_from_availability_selection(
        request(),
        source_workflow_run="37714773301",
        artifact_name="cash-stage2-selection-control",
        artifact_id="11523362784",
        artifact_digest=(
            "sha256:d8118eae5d41eebe7b9f5c44c35acca4"
            "02043eb17682bd57acd7a9b613545f10"
        ),
    )
    return historical_selection_provenance_payload(provenance)


def test_availability_selection_replays_frozen_25_days() -> None:
    replay = replay_availability_selection(request())

    assert replay.population_size == 172
    assert replay.selected_market_dates == EXPECTED
    assert replay.evidence_sha256 == (
        "21a48dee14e352c5fbb2488661f45c6f"
        "e3e82e74a4759d9eba1347b0bbe6b4b7"
    )


def test_availability_selection_provenance_round_trips() -> None:
    payload = provenance_payload()

    provenance = parse_historical_selection_provenance(payload)

    assert provenance.selection_kind == "pre_registered_availability_sample"
    assert provenance.strategy == "cash-and-carry"
    assert provenance.seed is None
    assert provenance.excluded_market_dates == EXCLUDED
    assert provenance.selected_market_dates == EXPECTED
    assert historical_selection_provenance_payload(provenance) == payload


def test_availability_selection_provenance_fails_closed_on_drift() -> None:
    payload = provenance_payload()

    selected_drift = copy.deepcopy(payload)
    selected_drift["sampling"]["selected_market_dates"][0] = "2026-01-05"
    with pytest.raises(ValueError, match="market dates do not match"):
        parse_historical_selection_provenance(selected_drift)

    exclusion_drift = copy.deepcopy(payload)
    exclusion_drift["sampling"]["excluded_market_dates"].pop()
    with pytest.raises(ValueError, match="population_size"):
        parse_historical_selection_provenance(exclusion_drift)

    hash_drift = copy.deepcopy(payload)
    hash_drift["sampling"]["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence_sha256"):
        parse_historical_selection_provenance(hash_drift)


def test_availability_selection_counts_as_preregistered_reporting() -> None:
    view = _selection_provenance_view(
        {"selection_provenance": provenance_payload()},
        strategy="cash-and-carry",
        market_date="2026-03-28",
    )

    assert view["classification"] == "pre_registered_sample"
    assert (
        view["selection_kind"]
        == "pre_registered_availability_sample"
    )
