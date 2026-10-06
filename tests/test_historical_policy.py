import json
from pathlib import Path

import pytest

from future_opportunity.backtest.historical_policy import (
    collect_pinned_entry_market_days,
    distribution_transition_readiness,
    evaluate_historical_gate,
    load_historical_acceptance_policy,
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
