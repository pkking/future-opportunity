from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from future_opportunity.backtest.corpus import load_historical_corpus


@dataclass(frozen=True, slots=True)
class HistoricalAcceptancePolicy:
    policy_id: str
    mode: str
    required_gate_checks: tuple[str, ...]
    required_strategies: tuple[str, ...]
    minimum_distinct_market_days_per_strategy: int
    preferred_distinct_market_days_per_strategy: int
    requires_separate_adr: bool
    activation_requires_human_approval: bool


@dataclass(frozen=True, slots=True)
class Stage2DecisionQualityPolicy:
    adr: str
    status: str
    approved_at: str
    enabled_strategies: tuple[str, ...]
    economics_gate: str
    minimum_distinct_market_days: int
    preferred_threshold_freeze_days: int
    minimum_pre_registered_coverage_ratio: Decimal
    require_complete_expected_net_return_assessment: bool
    rejected_cases_remain_in_qualification_denominator: bool
    rejected_cases_are_not_realized_return_zero: bool
    market_wide_opportunity_arrival_rate_must_remain_unassessed: bool
    realized_return_gate_requires_future_human_approval: bool


@dataclass(frozen=True, slots=True)
class Stage2DecisionQualityReadiness:
    strategy: str
    enabled: bool
    pinned_day_count: int
    minimum_day_count: int
    pre_registered_day_count: int
    pre_registered_coverage_ratio: Decimal
    minimum_pre_registered_coverage_ratio: Decimal
    expected_net_return_assessed_count: int
    expected_net_return_assessment_complete: bool
    qualified_case_count: int
    realized_return_assessed_count: int
    decision_quality_ready: bool
    economics_gate: str
    realized_return_gate_available: bool
    market_wide_opportunity_arrival_rate: None
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HistoricalTransitionReadiness:
    required_strategies: tuple[str, ...]
    pinned_entry_market_days: tuple[tuple[str, tuple[str, ...]], ...]
    minimum_days_per_strategy: int
    preferred_days_per_strategy: int
    minimum_ready: bool
    preferred_ready: bool

    def counts(self) -> dict[str, int]:
        return {
            strategy: len(days)
            for strategy, days in self.pinned_entry_market_days
        }


def load_historical_acceptance_policy(
    path: Path,
) -> tuple[HistoricalAcceptancePolicy, dict[str, Any]]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise TypeError("historical target policy must be an object")
    if raw.get("schema_version") != 1:
        raise ValueError("unsupported historical target policy schema")

    policy_id = _required_string(raw, "policy_id")
    mode = _required_string(raw, "mode")
    if mode != "provenance_and_semantics":
        raise ValueError(f"unsupported historical acceptance mode: {mode}")

    reference = raw.get("reference_targets")
    if not isinstance(reference, dict):
        raise ValueError("historical policy is missing reference_targets")
    if reference.get("usage") != "reporting_only":
        raise ValueError(
            "deterministic reference targets must remain reporting_only "
            "for V0 historical acceptance"
        )
    if reference.get("must_not_gate_historical_returns") is not True:
        raise ValueError(
            "historical policy must forbid reference-return gating in V0"
        )

    checks = raw.get("required_gate_checks")
    if (
        not isinstance(checks, list)
        or not checks
        or not all(isinstance(item, str) and item for item in checks)
    ):
        raise ValueError("historical policy requires non-empty gate checks")

    transition = raw.get("transition_to_distribution_mode")
    if not isinstance(transition, dict):
        raise ValueError(
            "historical policy is missing distribution transition policy"
        )
    strategies = transition.get("required_strategies")
    if (
        not isinstance(strategies, list)
        or not strategies
        or not all(isinstance(item, str) and item for item in strategies)
    ):
        raise ValueError(
            "historical distribution transition requires strategy names"
        )

    minimum = _positive_int(
        transition,
        "minimum_distinct_market_days_per_strategy",
    )
    preferred = _positive_int(
        transition,
        "preferred_distinct_market_days_per_strategy",
    )
    if preferred < minimum:
        raise ValueError(
            "preferred historical day count must not be below minimum"
        )
    if transition.get("requires_separate_adr") is not True:
        raise ValueError(
            "distribution-mode transition must require a separate ADR"
        )
    if transition.get("activation_requires_human_approval") is not True:
        raise ValueError(
            "distribution-mode transition must require human approval"
        )
    if (
        transition.get(
            "thresholds_must_not_be_auto_derived_from_reference_targets"
        )
        is not True
    ):
        raise ValueError(
            "distribution thresholds must not be auto-derived "
            "from reference targets"
        )

    return (
        HistoricalAcceptancePolicy(
            policy_id=policy_id,
            mode=mode,
            required_gate_checks=tuple(checks),
            required_strategies=tuple(strategies),
            minimum_distinct_market_days_per_strategy=minimum,
            preferred_distinct_market_days_per_strategy=preferred,
            requires_separate_adr=True,
            activation_requires_human_approval=True,
        ),
        raw,
    )


def load_stage2_decision_quality_policy(
    raw_policy: Mapping[str, Any],
) -> Stage2DecisionQualityPolicy:
    raw = raw_policy.get("stage2_decision_quality")
    if not isinstance(raw, dict):
        raise ValueError("historical policy is missing stage2_decision_quality")
    enabled = raw.get("enabled_strategies")
    if (
        not isinstance(enabled, list)
        or not enabled
        or not all(isinstance(item, str) and item for item in enabled)
    ):
        raise ValueError("stage2 decision-quality policy requires enabled strategies")
    if raw.get("status") != "accepted":
        raise ValueError("stage2 decision-quality policy must be accepted")
    if raw.get("economics_gate") != "disabled":
        raise ValueError("stage2 economics gate must remain disabled")
    ratio_raw = raw.get("minimum_pre_registered_coverage_ratio")
    try:
        ratio = Decimal(str(ratio_raw))
    except Exception as ex:
        raise ValueError("invalid stage2 pre-registration coverage ratio") from ex
    if ratio < Decimal(0) or ratio > Decimal(1):
        raise ValueError("stage2 pre-registration coverage ratio must be within [0,1]")

    required_true = (
        "require_complete_expected_net_return_assessment",
        "rejected_cases_remain_in_qualification_denominator",
        "rejected_cases_are_not_realized_return_zero",
        "market_wide_opportunity_arrival_rate_must_remain_unassessed",
        "realized_return_gate_requires_future_human_approval",
    )
    for key in required_true:
        if raw.get(key) is not True:
            raise ValueError(f"stage2 decision-quality invariant must be true: {key}")

    return Stage2DecisionQualityPolicy(
        adr=_required_string(raw, "adr"),
        status="accepted",
        approved_at=_required_string(raw, "approved_at"),
        enabled_strategies=tuple(enabled),
        economics_gate="disabled",
        minimum_distinct_market_days=_positive_int(
            raw, "minimum_distinct_market_days"
        ),
        preferred_threshold_freeze_days=_positive_int(
            raw, "preferred_threshold_freeze_days"
        ),
        minimum_pre_registered_coverage_ratio=ratio,
        require_complete_expected_net_return_assessment=True,
        rejected_cases_remain_in_qualification_denominator=True,
        rejected_cases_are_not_realized_return_zero=True,
        market_wide_opportunity_arrival_rate_must_remain_unassessed=True,
        realized_return_gate_requires_future_human_approval=True,
    )


def stage2_decision_quality_readiness(
    policy: Stage2DecisionQualityPolicy,
    *,
    strategy: str,
    pinned_day_count: int,
    pre_registered_day_count: int,
    expected_net_return_assessed_count: int,
    qualified_case_count: int,
    realized_return_assessed_count: int,
) -> Stage2DecisionQualityReadiness:
    if pinned_day_count <= 0:
        raise ValueError("stage2 readiness requires pinned days")
    if not 0 <= pre_registered_day_count <= pinned_day_count:
        raise ValueError("invalid pre-registered day count")
    if not 0 <= expected_net_return_assessed_count <= pinned_day_count:
        raise ValueError("invalid expected-return assessed count")
    if not 0 <= qualified_case_count <= pinned_day_count:
        raise ValueError("invalid qualified-case count")
    if not 0 <= realized_return_assessed_count <= qualified_case_count:
        raise ValueError("invalid realized-return assessed count")

    enabled = strategy in policy.enabled_strategies
    coverage = Decimal(pre_registered_day_count) / Decimal(pinned_day_count)
    expected_complete = expected_net_return_assessed_count == pinned_day_count
    reasons: list[str] = []
    if not enabled:
        reasons.append("strategy_not_stage2_enabled")
    if pinned_day_count < policy.minimum_distinct_market_days:
        reasons.append("minimum_pinned_days_not_met")
    if coverage < policy.minimum_pre_registered_coverage_ratio:
        reasons.append("minimum_pre_registered_coverage_not_met")
    if (
        policy.require_complete_expected_net_return_assessment
        and not expected_complete
    ):
        reasons.append("expected_net_return_assessment_incomplete")

    ready = not reasons
    realized_available = qualified_case_count > 0 and (
        realized_return_assessed_count == qualified_case_count
    )
    return Stage2DecisionQualityReadiness(
        strategy=strategy,
        enabled=enabled,
        pinned_day_count=pinned_day_count,
        minimum_day_count=policy.minimum_distinct_market_days,
        pre_registered_day_count=pre_registered_day_count,
        pre_registered_coverage_ratio=coverage,
        minimum_pre_registered_coverage_ratio=(
            policy.minimum_pre_registered_coverage_ratio
        ),
        expected_net_return_assessed_count=expected_net_return_assessed_count,
        expected_net_return_assessment_complete=expected_complete,
        qualified_case_count=qualified_case_count,
        realized_return_assessed_count=realized_return_assessed_count,
        decision_quality_ready=ready,
        economics_gate=policy.economics_gate,
        realized_return_gate_available=realized_available,
        market_wide_opportunity_arrival_rate=None,
        reasons=tuple(reasons),
    )


def collect_pinned_entry_market_days(
    fixture_root: Path,
    *,
    required_strategies: tuple[str, ...],
) -> dict[str, tuple[str, ...]]:
    corpus = load_historical_corpus(
        index_path=fixture_root / "corpus-index.json",
        fixture_root=fixture_root,
        required_strategies=required_strategies,
    )
    grouped = corpus.entry_days_by_strategy()
    return {
        strategy: tuple(grouped.get(strategy, ()))
        for strategy in required_strategies
    }


def distribution_transition_readiness(
    policy: HistoricalAcceptancePolicy,
    pinned_days: Mapping[str, tuple[str, ...]],
) -> HistoricalTransitionReadiness:
    normalized = tuple(
        (
            strategy,
            tuple(pinned_days.get(strategy, ())),
        )
        for strategy in policy.required_strategies
    )
    counts = {
        strategy: len(days)
        for strategy, days in normalized
    }
    minimum_ready = all(
        counts[strategy]
        >= policy.minimum_distinct_market_days_per_strategy
        for strategy in policy.required_strategies
    )
    preferred_ready = all(
        counts[strategy]
        >= policy.preferred_distinct_market_days_per_strategy
        for strategy in policy.required_strategies
    )
    return HistoricalTransitionReadiness(
        required_strategies=policy.required_strategies,
        pinned_entry_market_days=normalized,
        minimum_days_per_strategy=(
            policy.minimum_distinct_market_days_per_strategy
        ),
        preferred_days_per_strategy=(
            policy.preferred_distinct_market_days_per_strategy
        ),
        minimum_ready=minimum_ready,
        preferred_ready=preferred_ready,
    )


def evaluate_historical_gate(
    policy: HistoricalAcceptancePolicy,
    checks: Mapping[str, bool],
) -> tuple[bool, dict[str, bool]]:
    evaluated: dict[str, bool] = {}
    for name in policy.required_gate_checks:
        value = checks.get(name)
        if not isinstance(value, bool):
            raise ValueError(
                f"required historical gate check is missing: {name}"
            )
        evaluated[name] = value
    return all(evaluated.values()), evaluated


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"historical policy {key} is required")
    return value


def _positive_int(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"historical policy {key} must be positive")
    return value
