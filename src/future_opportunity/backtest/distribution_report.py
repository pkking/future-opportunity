from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from future_opportunity.application.backtest.cash_and_carry import (
    CashAndCarryBacktestCaseResult,
    run_cash_and_carry_backtest,
)
from future_opportunity.application.backtest.funding_carry import (
    FundingCarryBacktestCaseResult,
    run_funding_carry_backtest,
)
from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.backtest.corpus import load_historical_corpus
from future_opportunity.backtest.fixture import (
    build_funding_case,
    load_funding_history_fixture,
)
from future_opportunity.backtest.historical_policy import (
    distribution_transition_readiness,
    load_historical_acceptance_policy,
    load_stage2_decision_quality_policy,
    stage2_decision_quality_readiness,
)
from future_opportunity.backtest.selection_provenance import (
    historical_selection_provenance_payload,
    validate_selection_provenance_for_market_date,
)
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
)
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
)


@dataclass(frozen=True, slots=True)
class DecimalDistribution:
    assessed_count: int
    minimum: Decimal | None
    p25: Decimal | None
    median: Decimal | None
    p90: Decimal | None
    maximum: Decimal | None
    mean: Decimal | None


def decimal_distribution(values: Iterable[Decimal]) -> DecimalDistribution:
    """Linear interpolation: sorted value at index (n-1) * percentile."""
    ordered = tuple(sorted(values))
    count = len(ordered)
    if count == 0:
        return DecimalDistribution(0, None, None, None, None, None, None)
    return DecimalDistribution(
        assessed_count=count,
        minimum=ordered[0],
        p25=_quantile(ordered, Decimal("0.25")),
        median=_quantile(ordered, Decimal("0.5")),
        p90=_quantile(ordered, Decimal("0.9")),
        maximum=ordered[-1],
        mean=sum(ordered, Decimal(0)) / Decimal(count),
    )


def _quantile(ordered: tuple[Decimal, ...], p: Decimal) -> Decimal:
    index = Decimal(len(ordered) - 1) * p
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - Decimal(lower)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _summary(
    results: tuple[FundingCarryBacktestCaseResult, ...]
    | tuple[CashAndCarryBacktestCaseResult, ...],
    *,
    strategy: str,
) -> dict[str, Any]:
    qualified = tuple(case for case in results if case.qualified)
    expected = decimal_distribution(case.expected_net_return for case in results)
    reason_counts: dict[str, int] = {}
    for case in results:
        if not case.qualified:
            for reason in case.qualification_reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

    if strategy == "funding-carry":
        funding_results = tuple(
            result for result in results if isinstance(result, FundingCarryBacktestCaseResult)
        )
        lower = decimal_distribution(
            result.realized_return_lower
            for result in funding_results
            if result.qualified and result.realized_return_lower is not None
        )
        upper = decimal_distribution(
            result.realized_return_upper
            for result in funding_results
            if result.qualified and result.realized_return_upper is not None
        )
        if lower.assessed_count != upper.assessed_count:
            raise ValueError("funding interval bound counts diverged")
        realized_count = lower.assessed_count
        return_distributions: dict[str, Any] = {
            "realized_return_interval_lower": asdict(lower),
            "realized_return_interval_upper": asdict(upper),
            "exact_realized_return": None,
            "note": "One-minute mark-price bounds; not exact funding settlement marks",
        }
    elif strategy == "cash-and-carry":
        cash_results = tuple(
            result for result in results if isinstance(result, CashAndCarryBacktestCaseResult)
        )
        realized = decimal_distribution(
            result.realized_net_return
            for result in cash_results
            if result.qualified
            and result.return_complete is True
            and result.realized_net_return is not None
        )
        realized_count = realized.assessed_count
        return_distributions = {
            "realized_net_return_with_complete_evidence": asdict(realized),
            "note": "Only qualified closed cases with complete return evidence",
        }
    else:
        raise ValueError(f"unsupported corpus reporting strategy: {strategy}")

    if len(results) == 0:
        raise ValueError("cannot summarize a strategy with zero pinned cases")
    if realized_count > len(qualified):
        raise ValueError("realized case count exceeds qualified case count")

    return {
        "strategy": strategy,
        "sample_unit": "one_frozen_case_per_pinned_entry_market_day",
        "pinned_entry_market_day_count": len(results),
        "evaluated_case_count": len(results),
        "qualified_case_count": len(qualified),
        "rejected_case_count": len(results) - len(qualified),
        "pinned_case_qualification_rate": (
            Decimal(len(qualified)) / Decimal(len(results))
        ),
        "market_wide_opportunity_arrival_rate": None,
        "qualified_cases_with_assessed_realized_return": realized_count,
        "qualified_cases_with_unassessed_realized_return": (
            len(qualified) - realized_count
        ),
        "expected_net_return_all_cases": asdict(expected),
        "realized_return": return_distributions,
        "qualification_reason_case_counts": dict(sorted(reason_counts.items())),
        "return_horizon": "per_case_not_annualized",
        "economics_gate": "reporting_only",
    }


def _selection_provenance_view(
    manifest: dict[str, Any],
    *,
    strategy: str,
    market_date: str,
) -> dict[str, Any]:
    raw = manifest.get("selection_provenance")
    if raw is None:
        return {
            "classification": "legacy_untracked",
            "selection_kind": None,
            "source": None,
            "sampling": None,
        }

    provenance = validate_selection_provenance_for_market_date(
        raw,
        strategy=strategy,
        market_date=market_date,
    )
    payload = historical_selection_provenance_payload(provenance)
    return {
        "classification": "pre_registered_sample",
        "selection_kind": provenance.selection_kind,
        "source": payload["source"],
        "sampling": payload["sampling"],
    }


def _selection_coverage(
    selection_by_dataset_id: dict[str, dict[str, Any]],
    *,
    entries_by_strategy: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    by_strategy: dict[str, Any] = {}
    total_pre_registered = 0
    total_legacy = 0

    for strategy, dataset_ids in entries_by_strategy.items():
        pre_registered = sum(
            1
            for dataset_id in dataset_ids
            if selection_by_dataset_id[dataset_id]["classification"]
            == "pre_registered_sample"
        )
        legacy = len(dataset_ids) - pre_registered
        total_pre_registered += pre_registered
        total_legacy += legacy
        by_strategy[strategy] = {
            "pinned_day_count": len(dataset_ids),
            "pre_registered_sample_day_count": pre_registered,
            "legacy_untracked_day_count": legacy,
            "pre_registered_coverage_ratio": (
                Decimal(pre_registered) / Decimal(len(dataset_ids))
                if dataset_ids
                else Decimal(0)
            ),
        }

    total = total_pre_registered + total_legacy
    return {
        "by_strategy": by_strategy,
        "total_pinned_day_count": total,
        "pre_registered_sample_day_count": total_pre_registered,
        "legacy_untracked_day_count": total_legacy,
        "pre_registered_coverage_ratio": (
            Decimal(total_pre_registered) / Decimal(total)
            if total
            else Decimal(0)
        ),
        "readiness_semantics": (
            "reporting_only; ADR-0007 readiness still counts all validated "
            "pinned entry-market days"
        ),
    }


def cash_expiry_horizon_cohorts(
    cases: tuple[CashAndCarryBacktestCaseResult, ...],
    *,
    pre_registered_case_ids: frozenset[str],
) -> dict[str, Any]:
    """Reporting-only expiry cohorts. Case outcomes are never used to select days."""
    if not cases:
        raise ValueError("cash cohort evidence requires pinned cases")

    grouped: dict[str, list[CashAndCarryBacktestCaseResult]] = {}
    horizons: dict[str, dict[str, Decimal]] = {}
    for case in cases:
        expiry = datetime.fromisoformat(case.expiry)
        entry = datetime.fromisoformat(case.observed_at)
        if case.exit_at is None:
            raise ValueError("Cash horizon evidence requires an explicit exit")
        exit_at = datetime.fromisoformat(case.exit_at)
        if entry.tzinfo is None or exit_at.tzinfo is None or expiry.tzinfo is None:
            raise ValueError("Cash horizon timestamps must be timezone aware")
        if not entry < exit_at < expiry:
            raise ValueError("Cash horizon must finish before contract expiry")
        duration = exit_at - entry
        days = (
            Decimal(duration.days)
            + Decimal(duration.seconds) / Decimal(86400)
            + Decimal(duration.microseconds) / Decimal(86400000000)
        )
        grouped.setdefault(case.expiry, []).append(case)
        per_expiry = horizons.setdefault(case.expiry, {})
        if case.case_id in per_expiry:
            raise ValueError("duplicate Cash case ID in expiry cohort")
        per_expiry[case.case_id] = days

    cohorts: list[dict[str, Any]] = []
    for expiry_at, group in sorted(grouped.items()):
        cohort = tuple(group)
        summary = _summary(cohort, strategy="cash-and-carry")
        durations = horizons[expiry_at]
        selected_count = sum(
            case.case_id in pre_registered_case_ids for case in cohort
        )
        cohorts.append(
            {
                "contract_expiry_at": expiry_at,
                "close_modes": sorted({case.close_mode for case in cohort}),
                "case_count": len(cohort),
                "pre_registered_case_count": selected_count,
                "pre_registered_coverage_ratio": (
                    Decimal(selected_count) / Decimal(len(cohort))
                ),
                "holding_days_all_cases": asdict(
                    decimal_distribution(durations.values())
                ),
                "holding_days_qualified_cases": asdict(
                    decimal_distribution(
                        durations[case.case_id]
                        for case in cohort
                        if case.qualified
                    )
                ),
                "summary": summary,
            }
        )

    return {
        "sample_unit": "one_frozen_case_per_pinned_entry_market_day",
        "cohort_key": "historical_contract_expiry_at",
        "cohort_count": len(cohorts),
        "shared_expiry_cases_are_independent_trials": False,
        "holding_days_are_realized_entry_to_exit_calendar_days": True,
        "return_horizon": "per_case_not_annualized",
        "market_wide_opportunity_arrival_rate": None,
        "economics_gate": "reporting_only",
        "note": (
            "Cases sharing a future contract expiry can overlap in holding "
            "period and market exposure. Qualified realized-return distributions "
            "are conditional, not annualized or independent investment trials."
        ),
        "cohorts": cohorts,
    }


async def build_historical_corpus_distribution(
    *,
    fixture_root: Path,
    index_path: Path,
    policy_path: Path,
    capital: Decimal = Decimal("10000"),
) -> dict[str, Any]:
    """Replay all indexed cases without inventing statistical acceptance targets."""
    if capital != Decimal("10000"):
        raise ValueError("pinned historical fixtures are frozen to 10000 USDT")

    policy, raw_policy = load_historical_acceptance_policy(policy_path)
    corpus = load_historical_corpus(
        index_path=index_path,
        fixture_root=fixture_root,
        required_strategies=policy.required_strategies,
    )
    funding_cases = []
    cash_cases = []
    provenance_by_id: dict[str, dict[str, Any]] = {}
    selection_by_dataset_id: dict[str, dict[str, Any]] = {}

    for entry in sorted(
        corpus.entries,
        key=lambda item: (item.strategy, item.entry_market_date, item.dataset_id),
    ):
        root = fixture_root / entry.fixture_path
        if entry.strategy == "funding-carry":
            fixture = load_funding_history_fixture(root)
            if len(fixture.alignment.samples) < 2:
                raise ValueError(
                    f"funding fixture requires two aligned observations: {entry.dataset_id}"
                )
            case = build_funding_case(
                fixture,
                entry_index=0,
                exit_index=len(fixture.alignment.samples) - 1,
            )
            funding_cases.append(case)
            source = fixture.manifest
            selection = _selection_provenance_view(
                source,
                strategy=entry.strategy,
                market_date=entry.entry_market_date,
            )
            selection_by_dataset_id[entry.dataset_id] = selection
            provenance_by_id[case.case_id] = {
                "dataset_id": entry.dataset_id,
                "entry_market_date": entry.entry_market_date,
                "fixture_path": entry.fixture_path,
                "source_artifact": source.get("derived_from_artifact"),
                "parent_alignment": source.get("parent_alignment"),
                "compact_alignment": source.get("alignment"),
                "selection": selection,
            }
        elif entry.strategy == "cash-and-carry":
            case = load_cash_and_carry_close_fixture(root)
            cash_cases.append(case)
            source = json.loads((root / "manifest.json").read_text())
            selection = _selection_provenance_view(
                source,
                strategy=entry.strategy,
                market_date=entry.entry_market_date,
            )
            selection_by_dataset_id[entry.dataset_id] = selection
            provenance_by_id[case.case_id] = {
                "dataset_id": entry.dataset_id,
                "entry_market_date": entry.entry_market_date,
                "fixture_path": entry.fixture_path,
                "source_artifact": source.get("derived_from_artifact"),
                "selection": selection,
            }
        else:
            raise ValueError(f"unsupported historical strategy: {entry.strategy}")

    if not funding_cases or not cash_cases:
        raise ValueError("corpus distribution requires both required strategies")

    funding_report = await run_funding_carry_backtest(
        tuple(funding_cases),
        capital=capital,
        assumptions=FundingCarryAssumptions(horizon_days=1),
    )
    cash_report = await run_cash_and_carry_backtest(
        tuple(cash_cases),
        capital=capital,
        assumptions=CashAndCarryAssumptions(),
    )
    readiness = distribution_transition_readiness(
        policy,
        corpus.entry_days_by_strategy(),
    )
    dataset_ids_by_strategy = {
        strategy: tuple(
            entry.dataset_id
            for entry in corpus.entries
            if entry.strategy == strategy
        )
        for strategy in policy.required_strategies
    }
    selection_coverage = _selection_coverage(
        selection_by_dataset_id,
        entries_by_strategy=dataset_ids_by_strategy,
    )

    results_by_strategy = {
        "funding-carry": funding_report.cases,
        "cash-and-carry": cash_report.cases,
    }
    summaries = {
        strategy: _summary(results_by_strategy[strategy], strategy=strategy)
        for strategy in policy.required_strategies
    }
    stage2_policy = load_stage2_decision_quality_policy(raw_policy)
    stage2 = {}
    for strategy in policy.required_strategies:
        summary = summaries[strategy]
        coverage = selection_coverage["by_strategy"][strategy]
        stage2[strategy] = asdict(
            stage2_decision_quality_readiness(
                stage2_policy,
                strategy=strategy,
                pinned_day_count=summary["pinned_entry_market_day_count"],
                pre_registered_day_count=coverage[
                    "pre_registered_sample_day_count"
                ],
                expected_net_return_assessed_count=summary[
                    "expected_net_return_all_cases"
                ]["assessed_count"],
                qualified_case_count=summary["qualified_case_count"],
                realized_return_assessed_count=summary[
                    "qualified_cases_with_assessed_realized_return"
                ],
            )
        )
    cash_cohorts = cash_expiry_horizon_cohorts(
        tuple(cash_report.cases),
        pre_registered_case_ids=frozenset(
            case.case_id
            for case in cash_report.cases
            if provenance_by_id[case.case_id]["selection"]["classification"]
            == "pre_registered_sample"
        ),
    )
    cases = {
        strategy: [
            {
                "provenance": provenance_by_id[result.case_id],
                "actual": asdict(result),
            }
            for result in results_by_strategy[strategy]
        ]
        for strategy in policy.required_strategies
    }
    return {
        "schema_version": 1,
        "evidence_type": "historical_corpus_distribution_actuals",
        "policy_id": policy.policy_id,
        "economics_gate": "reporting_only",
        "active_historical_gate": policy.mode,
        "case_sampling_semantics": (
            "one_frozen_entry_exit_case_per_pinned_market_day; "
            "not a market-wide opportunity arrival rate"
        ),
        "reference_targets_used_as_thresholds": False,
        "capital_usdt": capital,
        "readiness": asdict(readiness),
        "selection_provenance_coverage": selection_coverage,
        "stage2_decision_quality": {
            "adr": stage2_policy.adr,
            "status": stage2_policy.status,
            "approved_at": stage2_policy.approved_at,
            "strategy_approval_adrs": dict(stage2_policy.strategy_approval_adrs),
            "economics_gate": stage2_policy.economics_gate,
            "preferred_threshold_freeze_days": (
                stage2_policy.preferred_threshold_freeze_days
            ),
            "strategies": stage2,
        },
        "strategies": summaries,
        "cash_stage2_expiry_horizon_evidence": cash_cohorts,
        "cases": cases,
    }
