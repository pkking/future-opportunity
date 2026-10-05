from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping


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


def collect_pinned_entry_market_days(
    fixture_root: Path,
    *,
    required_strategies: tuple[str, ...],
) -> dict[str, tuple[str, ...]]:
    days: dict[str, set[str]] = {
        strategy: set()
        for strategy in required_strategies
    }
    for manifest_path in sorted(fixture_root.rglob("manifest.json")):
        raw = json.loads(manifest_path.read_text())
        if not isinstance(raw, dict):
            raise TypeError(
                f"historical fixture manifest must be an object: {manifest_path}"
            )
        strategy = raw.get("strategy")
        entry_market_date = raw.get("entry_market_date")
        if strategy is None and entry_market_date is None:
            continue
        if strategy not in days:
            raise ValueError(
                f"historical fixture has unsupported strategy: {strategy}"
            )
        if not isinstance(entry_market_date, str):
            raise ValueError(
                f"historical fixture entry_market_date missing: {manifest_path}"
            )
        try:
            parsed = date.fromisoformat(entry_market_date)
        except ValueError as error:
            raise ValueError(
                f"invalid entry_market_date in {manifest_path}"
            ) from error
        days[strategy].add(parsed.isoformat())

    return {
        strategy: tuple(sorted(values))
        for strategy, values in days.items()
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
