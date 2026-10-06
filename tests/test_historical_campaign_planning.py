from __future__ import annotations

from datetime import date, timedelta

import pytest

from future_opportunity.backtest.campaign_planning import (
    VerifiedHistoricalCandidate,
    plan_historical_campaigns,
)
from future_opportunity.backtest.corpus import (
    HistoricalCorpus,
    HistoricalCorpusEntry,
)
from future_opportunity.backtest.historical_policy import (
    HistoricalAcceptancePolicy,
)


POLICY = HistoricalAcceptancePolicy(
    policy_id="test-stage1",
    mode="provenance_and_semantics",
    required_gate_checks=("provenance",),
    required_strategies=("funding-carry", "cash-and-carry"),
    minimum_distinct_market_days_per_strategy=30,
    preferred_distinct_market_days_per_strategy=90,
    requires_separate_adr=True,
    activation_requires_human_approval=True,
)


def entry(strategy: str, day: str, dataset_id: str) -> HistoricalCorpusEntry:
    return HistoricalCorpusEntry(
        dataset_id=dataset_id,
        strategy=strategy,
        entry_market_date=day,
        fixture_path=dataset_id,
    )


def candidate(
    strategy: str,
    day: str,
    dataset_id: str,
    *,
    run: str = "100",
) -> VerifiedHistoricalCandidate:
    return VerifiedHistoricalCandidate(
        source_workflow_run=run,
        compact_artifact_name=f"compact-{dataset_id}",
        entry=entry(strategy, day, dataset_id),
    )


def corpus() -> HistoricalCorpus:
    return HistoricalCorpus(
        schema_version=1,
        entries=(
            entry("funding-carry", "2026-09-01", "funding-pinned"),
            entry("cash-and-carry", "2026-06-01", "cash-pinned"),
        ),
    )


def test_planner_excludes_pinned_and_keeps_projected_counts_separate() -> None:
    plan = plan_historical_campaigns(
        (
            candidate("funding-carry", "2026-09-03", "funding-new"),
            candidate("funding-carry", "2026-09-01", "funding-pinned"),
            candidate("cash-and-carry", "2026-06-03", "cash-new", run="101"),
        ),
        corpus=corpus(),
        policy=POLICY,
        campaign_prefix="verified-a",
    )
    assert len(plan.excluded_pinned) == 1
    assert dict(plan.pinned_counts) == {
        "funding-carry": 1,
        "cash-and-carry": 1,
    }
    assert dict(plan.projected_counts) == {
        "funding-carry": 2,
        "cash-and-carry": 2,
    }
    assert len(plan.waves) == 1
    assert [item.compact_artifact_name for item in plan.waves[0].items] == [
        "compact-funding-new",
        "compact-cash-new",
    ]
    assert plan.minimum_ready_now is False
    assert plan.minimum_ready_if_merged is False


def test_planner_splits_into_bounded_order_independent_waves() -> None:
    start = date(2026, 9, 2)
    candidates = tuple(
        candidate(
            "funding-carry",
            (start + timedelta(days=n)).isoformat(),
            f"funding-{n:02d}",
            run=str(200 + n),
        )
        for n in range(34)
    )
    forward = plan_historical_campaigns(
        candidates,
        corpus=corpus(),
        policy=POLICY,
        campaign_prefix="bulk-01",
    )
    backward = plan_historical_campaigns(
        tuple(reversed(candidates)),
        corpus=corpus(),
        policy=POLICY,
        campaign_prefix="bulk-01",
    )
    assert [wave.items for wave in forward.waves] == [
        wave.items for wave in backward.waves
    ]
    assert [len(wave.items) for wave in forward.waves] == [31, 3]
    assert [wave.campaign_id for wave in forward.waves] == [
        "bulk-01-wave-001",
        "bulk-01-wave-002",
    ]
    assert dict(forward.pinned_counts)["funding-carry"] == 1
    assert dict(forward.projected_counts)["funding-carry"] == 35
    assert forward.minimum_ready_if_merged is False  # Cash still at one day.


def test_planner_rejects_conflicting_pinned_strategy_date() -> None:
    with pytest.raises(ValueError, match="conflicts with pinned strategy/date"):
        plan_historical_campaigns(
            (candidate("funding-carry", "2026-09-01", "different"),),
            corpus=corpus(),
            policy=POLICY,
            campaign_prefix="conflict",
        )


def test_planner_rejects_duplicate_candidate_strategy_day_and_source() -> None:
    one = candidate("funding-carry", "2026-09-02", "funding-new")
    with pytest.raises(ValueError, match="duplicate candidate source"):
        plan_historical_campaigns(
            (one, one),
            corpus=corpus(),
            policy=POLICY,
            campaign_prefix="duplicate",
        )

    duplicate_date = candidate(
        "funding-carry",
        "2026-09-02",
        "other",
        run="201",
    )
    with pytest.raises(ValueError, match="duplicate candidate strategy/date"):
        plan_historical_campaigns(
            (one, duplicate_date),
            corpus=corpus(),
            policy=POLICY,
            campaign_prefix="duplicate-day",
        )


def test_planner_handles_noop_and_rejects_unsupported_strategy() -> None:
    plan = plan_historical_campaigns(
        (),
        corpus=corpus(),
        policy=POLICY,
        campaign_prefix="no-change",
    )
    assert plan.waves == ()
    assert plan.selected == ()
    assert plan.minimum_ready_now is False
    assert plan.projected_counts == plan.pinned_counts

    with pytest.raises(ValueError, match="unsupported strategy"):
        plan_historical_campaigns(
            (candidate("unknown", "2026-09-02", "unknown-id"),),
            corpus=corpus(),
            policy=POLICY,
            campaign_prefix="invalid",
        )
