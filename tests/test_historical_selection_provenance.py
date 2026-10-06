from __future__ import annotations

import copy

import pytest

from future_opportunity.backtest.sampling import (
    HistoricalSamplingRequest,
    historical_sampling_payload,
    sample_historical_market_days,
)
from future_opportunity.backtest.selection_provenance import (
    historical_selection_provenance_payload,
    parse_historical_selection_provenance,
    selection_provenance_from_sampling_evidence,
    validate_selection_provenance_for_market_date,
)


def golden_sampling() -> dict[str, object]:
    return historical_sampling_payload(
        sample_historical_market_days(
            HistoricalSamplingRequest(
                strategy="funding-carry",
                start_date="2026-01-01",
                end_date="2026-01-31",
                sample_size=5,
                seed="stage2-baseline-v1",
            )
        )
    )


def golden_provenance_payload() -> dict[str, object]:
    provenance = selection_provenance_from_sampling_evidence(
        golden_sampling(),
        source_workflow_run="37482498880",
        artifact_name="historical-market-day-sample-37482498880",
        artifact_id="11421537670",
        artifact_digest=(
            "sha256:bdaab43d0be70a2fc8b43059d39f5341"
            "a2405bf9a0aff00306b90e92e24b8fa2"
        ),
    )
    return historical_selection_provenance_payload(provenance)


def test_selection_provenance_round_trips_and_replays_sample() -> None:
    payload = golden_provenance_payload()

    provenance = parse_historical_selection_provenance(payload)

    assert provenance.strategy == "funding-carry"
    assert provenance.source.workflow_run == "37482498880"
    assert provenance.source.artifact_id == "11421537670"
    assert provenance.selected_market_dates == (
        "2026-01-01",
        "2026-01-08",
        "2026-01-13",
        "2026-01-22",
        "2026-01-29",
    )
    assert provenance.contains_market_date("2026-01-13") is True
    assert provenance.contains_market_date("2026-01-14") is False
    assert historical_selection_provenance_payload(provenance) == payload


def test_selection_provenance_rejects_selected_date_seed_and_evidence_hash_drift() -> None:
    selected_drift = copy.deepcopy(golden_provenance_payload())
    selected_drift["sampling"]["selected_market_dates"][0] = "2026-01-02"
    with pytest.raises(ValueError, match="market dates do not match"):
        parse_historical_selection_provenance(selected_drift)

    seed_drift = copy.deepcopy(golden_provenance_payload())
    seed_drift["sampling"]["seed"] = "changed-after-outcomes"
    with pytest.raises(ValueError, match="market dates do not match"):
        parse_historical_selection_provenance(seed_drift)

    sha_drift = copy.deepcopy(golden_provenance_payload())
    sha_drift["sampling"]["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence_sha256"):
        parse_historical_selection_provenance(sha_drift)


def test_selection_provenance_rejects_source_and_schema_drift() -> None:
    unsafe = copy.deepcopy(golden_provenance_payload())
    unsafe["source"]["artifact_name"] = "../sample"
    with pytest.raises(ValueError, match="safe name"):
        parse_historical_selection_provenance(unsafe)

    wrong_run = copy.deepcopy(golden_provenance_payload())
    wrong_run["source"]["workflow_run"] = "not-a-run"
    with pytest.raises(ValueError, match="numeric"):
        parse_historical_selection_provenance(wrong_run)

    schema = copy.deepcopy(golden_provenance_payload())
    schema["unexpected"] = True
    with pytest.raises(ValueError, match="fields differ"):
        parse_historical_selection_provenance(schema)


def test_selection_provenance_preserves_cash_strategy_hash_domain() -> None:
    raw = historical_sampling_payload(
        sample_historical_market_days(
            HistoricalSamplingRequest(
                strategy="cash-and-carry",
                start_date="2026-04-01",
                end_date="2026-04-30",
                sample_size=4,
                seed="cash-stage2-v1",
            )
        )
    )
    provenance = selection_provenance_from_sampling_evidence(
        raw,
        source_workflow_run="123",
        artifact_name="cash-sample-123",
        artifact_id="456",
        artifact_digest="a" * 64,
    )

    assert provenance.strategy == "cash-and-carry"
    assert provenance.source.artifact_digest == "sha256:" + "a" * 64
    assert len(provenance.selected_market_dates) == 4


def test_selection_provenance_market_date_validation_is_strategy_specific() -> None:
    payload = golden_provenance_payload()

    accepted = validate_selection_provenance_for_market_date(
        payload,
        strategy="funding-carry",
        market_date="2026-01-13",
    )
    assert accepted.contains_market_date("2026-01-13")

    with pytest.raises(ValueError, match="strategy mismatch"):
        validate_selection_provenance_for_market_date(
            payload,
            strategy="cash-and-carry",
            market_date="2026-01-13",
        )

    with pytest.raises(ValueError, match="outside selection provenance"):
        validate_selection_provenance_for_market_date(
            payload,
            strategy="funding-carry",
            market_date="2026-01-14",
        )
