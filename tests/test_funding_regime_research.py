from __future__ import annotations

import copy
from datetime import date, timedelta

import pytest

from future_opportunity.backtest.funding_regime_research import (
    REGIMES,
    plan_funding_regime_research,
)


def input_evidence() -> dict:
    start = date(2026, 1, 1)
    rows = []
    # Two days per regime; no outcomes or post-entry features.
    for i in range(8):
        day = start + timedelta(days=i)
        previous = day - timedelta(days=1)
        funding = "-0.0001" if i // 2 < 2 else "0.0001"
        volatility = "50" if i // 2 in (0, 2) else "120"
        rows.append(
            {
                "market_date": day.isoformat(),
                "entry_at": f"{day.isoformat()}T00:15:00+00:00",
                "features_observed_at": f"{previous.isoformat()}T23:59:00+00:00",
                "funding_observed_at": f"{previous.isoformat()}T16:00:00+00:00",
                "volatility_window_end_at": f"{previous.isoformat()}T23:00:00+00:00",
                "lagged_funding_rate": funding,
                "trailing_spot_volatility_bps": volatility,
                "source_record_id": f"okx-pre-entry-{day}",
                "source_record_sha256": f"{i + 1:064x}",
            }
        )
    return {
        "schema_version": 1,
        "evidence_type": "funding_pre_entry_regime_features",
        "policy_version": "pre-entry-funding-regime-research-v1",
        "seed": "approved-before-outcome-observation-v1",
        "start_date": "2026-01-01",
        "end_date": "2026-01-08",
        "requested_per_regime": 1,
        "source": {
            "provider": "OKX",
            "instrument_id": "BTC-USDT-SWAP",
            "artifact_digest": "sha256:" + "a" * 64,
            "observation_contract": "pre_entry_observed_not_outcome",
        },
        "pinned_market_dates": [],
        "missing_market_dates": [],
        "observations": rows,
    }


def test_deterministic_four_regime_research_selection() -> None:
    evidence = input_evidence()
    result = plan_funding_regime_research(evidence)
    assert result == plan_funding_regime_research(copy.deepcopy(evidence))
    assert [x["name"] for x in result["regimes"]] == list(REGIMES)
    assert [x["eligible_count"] for x in result["regimes"]] == [2] * 4
    assert [x["selected_count"] for x in result["regimes"]] == [1] * 4
    assert len(result["selected_dates"]) == 4
    assert result["quota_fully_met"] is True
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False
    assert result["source_authentication_status"] == "requires_independent_review"
    assert result["selection_uses_qualified_or_return_outcomes"] is False


def test_never_silently_replace_insufficient_strata() -> None:
    evidence = input_evidence()
    evidence["pinned_market_dates"] = ["2026-01-01", "2026-01-02"]
    result = plan_funding_regime_research(evidence)
    assert result["quota_fully_met"] is False
    assert result["regimes"][0]["quota_shortfall"] == 1
    assert result["regimes"][0]["selected_dates"] == []


def test_missing_feature_dates_must_be_declared() -> None:
    evidence = input_evidence()
    evidence["observations"].pop(0)
    with pytest.raises(ValueError, match="every study day"):
        plan_funding_regime_research(evidence)
    evidence["missing_market_dates"] = ["2026-01-01"]
    result = plan_funding_regime_research(evidence)
    assert result["missing_dates"] == ["2026-01-01"]


def test_duplicate_or_future_date_leakage_is_rejected() -> None:
    evidence = input_evidence()
    evidence["observations"].append(copy.deepcopy(evidence["observations"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        plan_funding_regime_research(evidence)
    evidence["observations"].pop()
    evidence["observations"][0]["features_observed_at"] = "2026-01-01T01:00:00+00:00"
    with pytest.raises(ValueError, match="before entry"):
        plan_funding_regime_research(evidence)


def test_funding_event_and_volatility_window_must_precede_entry() -> None:
    evidence = input_evidence()
    evidence["observations"][0]["funding_observed_at"] = "2026-01-01T00:30:00+00:00"
    with pytest.raises(ValueError, match="before entry"):
        plan_funding_regime_research(evidence)
    evidence = input_evidence()
    evidence["observations"][0]["volatility_window_end_at"] = "2026-01-01T01:00:00+00:00"
    with pytest.raises(ValueError, match="before entry"):
        plan_funding_regime_research(evidence)


def test_unknown_outcome_fields_and_invalid_digest_are_rejected() -> None:
    evidence = input_evidence()
    evidence["observations"][0]["realized_net_return"] = "0.1"
    with pytest.raises(ValueError, match="row fields"):
        plan_funding_regime_research(evidence)
    evidence = input_evidence()
    evidence["source"]["artifact_digest"] = "sha256:unverified"
    with pytest.raises(ValueError, match="SHA-256"):
        plan_funding_regime_research(evidence)


def test_non_finite_values_and_incorrect_entry_time_fail_closed() -> None:
    evidence = input_evidence()
    evidence["observations"][0]["trailing_spot_volatility_bps"] = "NaN"
    with pytest.raises(ValueError, match="finite"):
        plan_funding_regime_research(evidence)
    evidence = input_evidence()
    evidence["observations"][0]["entry_at"] = "2026-01-01T01:15:00+00:00"
    with pytest.raises(ValueError, match="00:15"):
        plan_funding_regime_research(evidence)


def test_provenance_seed_and_corpus_exclusions_change_research_digest() -> None:
    evidence = input_evidence()
    base = plan_funding_regime_research(evidence)
    evidence["seed"] = "different-fixed-seed"
    modified = plan_funding_regime_research(evidence)
    assert modified["evidence_sha256"] != base["evidence_sha256"]
    evidence = input_evidence()
    evidence["pinned_market_dates"] = ["2026-01-01"]
    modified = plan_funding_regime_research(evidence)
    assert modified["input_sha256"] != base["input_sha256"]
