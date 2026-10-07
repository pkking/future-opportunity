from __future__ import annotations

from datetime import date, timedelta

import pytest

from future_opportunity.backtest.historical_policy import HistoricalAcceptancePolicy
from future_opportunity.backtest.pending_review import (
    PendingCorpusProposal,
    analyze_pending_corpus_prs,
    parse_corpus_index_snapshot,
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
SHA3 = "a" * 40
SHA4 = "b" * 40


def row(strategy: str, market_day: str) -> dict[str, str]:
    dataset_id = f"{strategy}-{market_day}"
    return {
        "strategy": strategy,
        "entry_market_date": market_day,
        "dataset_id": dataset_id,
        "fixture_path": dataset_id,
    }


BASELINE = [
    row("funding-carry", "2026-09-01"),
    row("funding-carry", "2026-09-02"),
    row("cash-and-carry", "2026-06-01"),
    row("cash-and-carry", "2026-06-02"),
]
PR3_ADDITIONS = [
    row("funding-carry", "2026-09-03"),
    row("cash-and-carry", "2026-06-03"),
]
PR4_ADDITIONS = [
    *(row("funding-carry", f"2026-01-{day:02d}") for day in (1, 8, 13, 22, 29)),
    row("cash-and-carry", "2026-06-04"),
    row("cash-and-carry", "2026-06-08"),
]


def snapshot(items: list[dict[str, str]]):
    return parse_corpus_index_snapshot(
        {"schema_version": 1, "entries": items},
        required_strategies=POLICY.required_strategies,
    )


def proposal(number: int, additions: list[dict[str, str]]) -> PendingCorpusProposal:
    return PendingCorpusProposal(
        pr_number=number,
        head_sha=SHA3 if number == 3 else SHA4,
        index=snapshot(BASELINE + additions),
    )


def test_pending_pr_review_separates_main_counts_from_two_pr_projection() -> None:
    report = analyze_pending_corpus_prs(
        snapshot(BASELINE),
        (proposal(4, PR4_ADDITIONS), proposal(3, PR3_ADDITIONS)),
        policy=POLICY,
    )

    assert dict(report.pinned_counts) == {
        "funding-carry": 2,
        "cash-and-carry": 2,
    }
    assert dict(report.projected_union_counts_if_all_approved) == {
        "funding-carry": 8,
        "cash-and-carry": 5,
    }
    assert [(change.pr_number, len(change.proposed_additions)) for change in report.proposals] == [
        (3, 2),
        (4, 7),
    ]
    assert report.overlaps == ()
    assert report.conflicting_pending_facts is False
    assert report.shared_index_reconciliation_required is True
    assert report.minimum_ready_now is False
    assert report.minimum_ready_if_all_approved is False
    assert report.to_payload()["unmerged_proposals_count_toward_pinned"] is False
    assert report.to_payload()["remote_fixture_content_verified_by_this_report"] is False


def test_identical_pending_day_deduplicates_but_still_flags_overlap() -> None:
    first = proposal(3, [row("funding-carry", "2026-09-03")])
    second = proposal(4, [row("funding-carry", "2026-09-03")])
    report = analyze_pending_corpus_prs(
        snapshot(BASELINE), (first, second), policy=POLICY
    )

    assert dict(report.projected_union_counts_if_all_approved)["funding-carry"] == 3
    assert len(report.overlaps) == 1
    overlap = report.overlaps[0]
    assert overlap.pr_numbers == (3, 4)
    assert overlap.conflict is False
    assert report.conflicting_pending_facts is False


def test_conflicting_pending_strategy_date_detected_without_double_count() -> None:
    different = row("funding-carry", "2026-09-03")
    different["dataset_id"] += "-other"
    different["fixture_path"] += "-other"
    report = analyze_pending_corpus_prs(
        snapshot(BASELINE),
        (
            proposal(3, [row("funding-carry", "2026-09-03")]),
            proposal(4, [different]),
        ),
        policy=POLICY,
    )

    assert report.conflicting_pending_facts is True
    assert report.overlaps[0].conflict is True
    assert len(report.overlaps[0].dataset_ids) == 2
    assert dict(report.projected_union_counts_if_all_approved)["funding-carry"] == 3


def test_pending_pr_cannot_omit_or_rewrite_current_baseline() -> None:
    missing = PendingCorpusProposal(
        pr_number=3, head_sha=SHA3, index=snapshot(BASELINE[1:])
    )
    with pytest.raises(ValueError, match="omits pinned"):
        analyze_pending_corpus_prs(snapshot(BASELINE), (missing,), policy=POLICY)

    mutated = [dict(item) for item in BASELINE]
    mutated[0]["dataset_id"] = "changed"
    with pytest.raises(ValueError, match="changes pinned"):
        analyze_pending_corpus_prs(
            snapshot(BASELINE),
            (PendingCorpusProposal(pr_number=3, head_sha=SHA3, index=snapshot(mutated)),),
            policy=POLICY,
        )


def test_proposal_cannot_reuse_another_pinned_dataset_identity() -> None:
    colliding = row("funding-carry", "2026-09-03")
    colliding["dataset_id"] = BASELINE[0]["dataset_id"]
    with pytest.raises(ValueError, match="duplicate corpus dataset_id"):
        analyze_pending_corpus_prs(
            snapshot(BASELINE), (proposal(3, [colliding]),), policy=POLICY
        )


def test_index_snapshot_rejects_duplicate_unsafe_and_noncanonical_values() -> None:
    with pytest.raises(ValueError, match="duplicate corpus strategy/date"):
        snapshot(BASELINE + [dict(BASELINE[0])])

    traversal = row("funding-carry", "2026-09-03")
    traversal["fixture_path"] = "../bad"
    with pytest.raises(ValueError, match="safe directory"):
        snapshot(BASELINE + [traversal])

    invalid = row("funding-carry", "2026-09-03")
    invalid["entry_market_date"] = "2026/09/03"
    with pytest.raises(ValueError, match="entry_market_date"):
        snapshot(BASELINE + [invalid])

    with pytest.raises(ValueError, match="unsupported corpus strategy"):
        snapshot(BASELINE + [row("other", "2026-09-04")])


def test_readiness_projection_still_requires_both_strategies() -> None:
    start = date(2026, 1, 1)
    funding_added = [
        row("funding-carry", (start + timedelta(days=n)).isoformat())
        for n in range(28)
    ]
    report = analyze_pending_corpus_prs(
        snapshot(BASELINE), (proposal(3, funding_added),), policy=POLICY
    )
    assert dict(report.projected_union_counts_if_all_approved)["funding-carry"] == 30
    assert dict(report.projected_union_counts_if_all_approved)["cash-and-carry"] == 2
    assert report.minimum_ready_if_all_approved is False


def test_duplicate_pr_number_fails_closed() -> None:
    one = proposal(3, PR3_ADDITIONS)
    with pytest.raises(ValueError, match="duplicate pending PR number"):
        analyze_pending_corpus_prs(snapshot(BASELINE), (one, one), policy=POLICY)
