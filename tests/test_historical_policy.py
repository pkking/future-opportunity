import json
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.backtest.historical_policy import (
    collect_pinned_entry_market_days,
    distribution_transition_readiness,
    evaluate_historical_gate,
    load_historical_acceptance_policy,
    load_stage2_decision_quality_policy,
    stage2_decision_quality_readiness,
)


ROOT = Path(__file__).parents[1]
POLICY = ROOT / "tests/e2e/historical-target-policy.json"
FIXTURES = ROOT / "tests/fixtures/historical"
INDEX = FIXTURES / "corpus-index.json"


def test_repository_historical_policy_is_v0_provenance_semantics() -> None:
    policy, raw = load_historical_acceptance_policy(POLICY)

    assert policy.policy_id == "historical-acceptance-v0"
    assert policy.mode == "provenance_and_semantics"
    assert raw["reference_targets"]["usage"] == "reporting_only"
    assert policy.minimum_distinct_market_days_per_strategy == 30
    assert policy.preferred_distinct_market_days_per_strategy == 90
    assert policy.requires_separate_adr is True
    assert policy.activation_requires_human_approval is True


def test_distribution_readiness_counts_pinned_entry_market_days() -> None:
    policy, _ = load_historical_acceptance_policy(POLICY)
    days = collect_pinned_entry_market_days(
        FIXTURES,
        required_strategies=policy.required_strategies,
    )
    readiness = distribution_transition_readiness(policy, days)

    raw = json.loads(INDEX.read_text())
    expected_days = {
        strategy: tuple(
            sorted(
                entry["entry_market_date"]
                for entry in raw["entries"]
                if entry["strategy"] == strategy
            )
        )
        for strategy in policy.required_strategies
    }

    assert days == expected_days
    assert readiness.counts() == {
        strategy: len(expected_days[strategy])
        for strategy in policy.required_strategies
    }
    assert readiness.minimum_ready is (
        all(
            len(expected_days[strategy])
            >= policy.minimum_distinct_market_days_per_strategy
            for strategy in policy.required_strategies
        )
    )
    assert readiness.preferred_ready is (
        all(
            len(expected_days[strategy])
            >= policy.preferred_distinct_market_days_per_strategy
            for strategy in policy.required_strategies
        )
    )


def test_historical_gate_requires_every_versioned_check() -> None:
    policy, _ = load_historical_acceptance_policy(POLICY)
    all_true = {
        name: True
        for name in policy.required_gate_checks
    }

    passed, evaluated = evaluate_historical_gate(policy, all_true)

    assert passed is True
    assert evaluated == all_true

    one_false = dict(all_true)
    one_false[policy.required_gate_checks[0]] = False
    passed, _ = evaluate_historical_gate(policy, one_false)
    assert passed is False

    missing = dict(all_true)
    missing.pop(policy.required_gate_checks[0])
    with pytest.raises(ValueError, match="required historical gate check"):
        evaluate_historical_gate(policy, missing)


def test_policy_rejects_using_reference_returns_as_historical_gate(
    tmp_path: Path,
) -> None:
    raw = json.loads(POLICY.read_text())
    raw["reference_targets"]["usage"] = "gating"
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(raw))

    with pytest.raises(ValueError, match="reporting_only"):
        load_historical_acceptance_policy(path)


def test_policy_rejects_automatic_distribution_transition(
    tmp_path: Path,
) -> None:
    raw = json.loads(POLICY.read_text())
    raw["transition_to_distribution_mode"][
        "activation_requires_human_approval"
    ] = False
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(raw))

    with pytest.raises(ValueError, match="human approval"):
        load_historical_acceptance_policy(path)


def test_accepted_stage2_decision_quality_policy_is_explicit() -> None:
    _, raw = load_historical_acceptance_policy(POLICY)
    stage2 = load_stage2_decision_quality_policy(raw)

    assert stage2.adr == "ADR-0008"
    assert stage2.status == "accepted"
    assert stage2.enabled_strategies == ("funding-carry",)
    assert stage2.economics_gate == "disabled"
    assert stage2.minimum_distinct_market_days == 30
    assert stage2.preferred_threshold_freeze_days == 90
    assert str(stage2.minimum_pre_registered_coverage_ratio) == "0.80"
    assert stage2.realized_return_gate_requires_future_human_approval is True


def test_funding_stage2_decision_quality_can_be_ready_with_zero_qualified() -> None:
    _, raw = load_historical_acceptance_policy(POLICY)
    stage2 = load_stage2_decision_quality_policy(raw)

    readiness = stage2_decision_quality_readiness(
        stage2,
        strategy="funding-carry",
        pinned_day_count=32,
        pre_registered_day_count=29,
        expected_net_return_assessed_count=32,
        qualified_case_count=0,
        realized_return_assessed_count=0,
    )

    assert readiness.enabled is True
    assert readiness.decision_quality_ready is True
    assert readiness.reasons == ()
    assert readiness.economics_gate == "disabled"
    assert readiness.realized_return_gate_available is False
    assert readiness.market_wide_opportunity_arrival_rate is None


def test_cash_stage2_remains_disabled_below_minimum() -> None:
    _, raw = load_historical_acceptance_policy(POLICY)
    stage2 = load_stage2_decision_quality_policy(raw)

    readiness = stage2_decision_quality_readiness(
        stage2,
        strategy="cash-and-carry",
        pinned_day_count=5,
        pre_registered_day_count=3,
        expected_net_return_assessed_count=5,
        qualified_case_count=0,
        realized_return_assessed_count=0,
    )

    assert readiness.enabled is False
    assert readiness.decision_quality_ready is False
    assert "strategy_not_stage2_enabled" in readiness.reasons
    assert "minimum_pinned_days_not_met" in readiness.reasons


def test_cash_stage2_evidence_can_meet_conditions_without_approval() -> None:
    _, raw = load_historical_acceptance_policy(POLICY)
    policy = load_stage2_decision_quality_policy(raw)

    readiness = stage2_decision_quality_readiness(
        policy,
        strategy="cash-and-carry",
        pinned_day_count=30,
        pre_registered_day_count=27,
        expected_net_return_assessed_count=30,
        qualified_case_count=8,
        realized_return_assessed_count=8,
    )

    assert readiness.evidence_requirements_met is True
    assert readiness.evidence_reasons == ()
    assert readiness.pre_registered_coverage_ratio == Decimal("0.9")
    assert readiness.realized_return_gate_available is True
    assert readiness.enabled is False
    assert readiness.decision_quality_ready is False
    assert readiness.economics_gate == "disabled"
    assert readiness.reasons == ("strategy_not_stage2_enabled",)


def test_cash_stage2_insufficient_evidence_reports_independent_failures() -> None:
    _, raw = load_historical_acceptance_policy(POLICY)
    policy = load_stage2_decision_quality_policy(raw)

    readiness = stage2_decision_quality_readiness(
        policy,
        strategy="cash-and-carry",
        pinned_day_count=29,
        pre_registered_day_count=20,
        expected_net_return_assessed_count=28,
        qualified_case_count=2,
        realized_return_assessed_count=0,
    )

    assert readiness.evidence_requirements_met is False
    assert readiness.evidence_reasons == (
        "minimum_pinned_days_not_met",
        "minimum_pre_registered_coverage_not_met",
        "expected_net_return_assessment_incomplete",
    )
    assert readiness.reasons == (
        "strategy_not_stage2_enabled",
        *readiness.evidence_reasons,
    )
    assert readiness.decision_quality_ready is False
    assert readiness.realized_return_gate_available is False
