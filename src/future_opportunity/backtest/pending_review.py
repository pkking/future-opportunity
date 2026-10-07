"""Read-only review of multiple unmerged historical corpus PR index snapshots."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from future_opportunity.backtest.corpus import HistoricalCorpusEntry
from future_opportunity.backtest.historical_policy import HistoricalAcceptancePolicy


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_HEAD_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass(frozen=True, slots=True)
class CorpusIndexSnapshot:
    entries: tuple[HistoricalCorpusEntry, ...]


@dataclass(frozen=True, slots=True)
class PendingCorpusProposal:
    pr_number: int
    head_sha: str
    index: CorpusIndexSnapshot

    def __post_init__(self) -> None:
        if type(self.pr_number) is not int or self.pr_number <= 0:
            raise ValueError("pending PR number must be positive")
        if _HEAD_SHA.fullmatch(self.head_sha) is None:
            raise ValueError("pending PR head_sha must be a 40-character hex SHA")


@dataclass(frozen=True, slots=True)
class PendingCorpusPrChange:
    pr_number: int
    head_sha: str
    proposed_additions: tuple[HistoricalCorpusEntry, ...]
    baseline_entries_preserved: int


@dataclass(frozen=True, slots=True)
class PendingCorpusOverlap:
    strategy: str
    entry_market_date: str
    pr_numbers: tuple[int, ...]
    dataset_ids: tuple[str, ...]
    conflict: bool


@dataclass(frozen=True, slots=True)
class PendingCorpusReview:
    evidence_type: str
    evidence_scope: str
    pinned_counts: tuple[tuple[str, int], ...]
    projected_union_counts_if_all_approved: tuple[tuple[str, int], ...]
    minimum_ready_now: bool
    minimum_ready_if_all_approved: bool
    preferred_ready_now: bool
    preferred_ready_if_all_approved: bool
    proposals: tuple[PendingCorpusPrChange, ...]
    overlaps: tuple[PendingCorpusOverlap, ...]
    conflicting_pending_facts: bool
    shared_index_reconciliation_required: bool

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = 1
        payload["unmerged_proposals_count_toward_pinned"] = False
        payload["remote_fixture_content_verified_by_this_report"] = False
        payload["mergeability_verified_by_this_report"] = False
        payload["review_note"] = (
            "Proposal indexes are read-only identity evidence, not validated "
            "remote fixture bytes. Require each PR's CI and Historical Smoke. "
            "Revalidate remaining review branches after any corpus merge."
        )
        payload["pinned_counts"] = dict(self.pinned_counts)
        payload["projected_union_counts_if_all_approved"] = dict(
            self.projected_union_counts_if_all_approved
        )
        return payload


def parse_corpus_index_snapshot(
    raw: Any,
    *,
    required_strategies: tuple[str, ...],
) -> CorpusIndexSnapshot:
    """Validate metadata only; never claim this verified referenced files."""
    if not isinstance(raw, dict):
        raise TypeError("corpus index snapshot must be an object")
    if set(raw) != {"schema_version", "entries"}:
        raise ValueError("corpus index snapshot has unexpected fields")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("unsupported corpus index snapshot schema")
    raw_entries = raw["entries"]
    if not isinstance(raw_entries, list):
        raise TypeError("corpus index entries must be a list")

    entries: list[HistoricalCorpusEntry] = []
    seen_ids: set[str] = set()
    seen_dates: set[tuple[str, str]] = set()
    seen_paths: set[str] = set()
    for position, value in enumerate(raw_entries):
        if not isinstance(value, dict):
            raise TypeError(f"corpus index entry {position} must be an object")
        expected = {
            "dataset_id",
            "strategy",
            "entry_market_date",
            "fixture_path",
        }
        if set(value) != expected:
            raise ValueError(f"corpus index entry {position} fields differ")
        for key in expected:
            if not isinstance(value[key], str) or not value[key]:
                raise ValueError(f"corpus index entry {position} invalid {key}")

        strategy = value["strategy"]
        market_date = value["entry_market_date"]
        dataset_id = value["dataset_id"]
        fixture_path = value["fixture_path"]
        if strategy not in required_strategies:
            raise ValueError(f"unsupported corpus strategy: {strategy}")
        if _SAFE_ID.fullmatch(dataset_id) is None:
            raise ValueError("corpus dataset_id must be a safe identifier")
        if _SAFE_ID.fullmatch(fixture_path) is None:
            raise ValueError("corpus fixture_path must be a safe directory")
        try:
            canonical_date = date.fromisoformat(market_date).isoformat()
        except ValueError as error:
            raise ValueError("corpus entry_market_date is invalid") from error
        if canonical_date != market_date:
            raise ValueError("corpus entry_market_date must be canonical")

        key = (strategy, market_date)
        if key in seen_dates:
            raise ValueError(f"duplicate corpus strategy/date: {key}")
        if dataset_id in seen_ids:
            raise ValueError(f"duplicate corpus dataset_id: {dataset_id}")
        if fixture_path in seen_paths:
            raise ValueError(f"duplicate corpus fixture_path: {fixture_path}")
        seen_ids.add(dataset_id)
        seen_dates.add(key)
        seen_paths.add(fixture_path)
        entries.append(
            HistoricalCorpusEntry(
                dataset_id=dataset_id,
                strategy=strategy,
                entry_market_date=market_date,
                fixture_path=fixture_path,
            )
        )
    return CorpusIndexSnapshot(entries=tuple(entries))


def analyze_pending_corpus_prs(
    baseline: CorpusIndexSnapshot,
    proposals: tuple[PendingCorpusProposal, ...],
    *,
    policy: HistoricalAcceptancePolicy,
) -> PendingCorpusReview:
    """Deduplicate pending facts while preserving the main-only pinned count."""
    required = policy.required_strategies
    baseline_by_day = {
        (entry.strategy, entry.entry_market_date): entry
        for entry in baseline.entries
    }
    baseline_ids = {entry.dataset_id for entry in baseline.entries}
    baseline_paths = {entry.fixture_path for entry in baseline.entries}

    seen_prs: set[int] = set()
    additions_by_day: dict[
        tuple[str, str], list[tuple[int, HistoricalCorpusEntry]]
    ] = {}
    changes: list[PendingCorpusPrChange] = []

    for proposal in sorted(proposals, key=lambda item: item.pr_number):
        if proposal.pr_number in seen_prs:
            raise ValueError(f"duplicate pending PR number: {proposal.pr_number}")
        seen_prs.add(proposal.pr_number)
        proposal_by_day = {
            (entry.strategy, entry.entry_market_date): entry
            for entry in proposal.index.entries
        }
        for key, baseline_entry in baseline_by_day.items():
            proposed = proposal_by_day.get(key)
            if proposed is None:
                raise ValueError(
                    f"pending PR #{proposal.pr_number} omits pinned "
                    f"strategy/date: {key}"
                )
            if proposed != baseline_entry:
                raise ValueError(
                    f"pending PR #{proposal.pr_number} changes pinned "
                    f"strategy/date identity: {key}"
                )
        added = tuple(
            sorted(
                (
                    entry
                    for entry in proposal.index.entries
                    if (entry.strategy, entry.entry_market_date)
                    not in baseline_by_day
                ),
                key=lambda entry: (
                    required.index(entry.strategy),
                    entry.entry_market_date,
                    entry.dataset_id,
                ),
            )
        )
        for entry in added:
            if entry.dataset_id in baseline_ids or entry.fixture_path in baseline_paths:
                raise ValueError(
                    f"pending PR #{proposal.pr_number} reuses pinned "
                    "dataset or fixture identity"
                )
            additions_by_day.setdefault(
                (entry.strategy, entry.entry_market_date), []
            ).append((proposal.pr_number, entry))
        changes.append(
            PendingCorpusPrChange(
                pr_number=proposal.pr_number,
                head_sha=proposal.head_sha,
                proposed_additions=added,
                baseline_entries_preserved=len(baseline.entries),
            )
        )

    overlaps: list[PendingCorpusOverlap] = []
    for (strategy, market_date), appearances in sorted(additions_by_day.items()):
        if len(appearances) < 2:
            continue
        distinct = {
            (entry.dataset_id, entry.fixture_path) for _, entry in appearances
        }
        overlaps.append(
            PendingCorpusOverlap(
                strategy=strategy,
                entry_market_date=market_date,
                pr_numbers=tuple(number for number, _ in appearances),
                dataset_ids=tuple(sorted({item[0] for item in distinct})),
                conflict=len(distinct) > 1,
            )
        )

    # The projected union counts only unique strategy/date pairs. Any overlap
    # must be reviewed; matching identity does not prove identical file bytes.
    union_days = set(baseline_by_day) | set(additions_by_day)
    pinned = tuple(
        (strategy, sum(key[0] == strategy for key in baseline_by_day))
        for strategy in required
    )
    projected = tuple(
        (strategy, sum(key[0] == strategy for key in union_days))
        for strategy in required
    )
    pinned_map = dict(pinned)
    projected_map = dict(projected)

    return PendingCorpusReview(
        evidence_type="pending_corpus_pr_review",
        evidence_scope="index_identity_only",
        pinned_counts=pinned,
        projected_union_counts_if_all_approved=projected,
        minimum_ready_now=all(
            pinned_map[strategy]
            >= policy.minimum_distinct_market_days_per_strategy
            for strategy in required
        ),
        minimum_ready_if_all_approved=all(
            projected_map[strategy]
            >= policy.minimum_distinct_market_days_per_strategy
            for strategy in required
        ),
        preferred_ready_now=all(
            pinned_map[strategy]
            >= policy.preferred_distinct_market_days_per_strategy
            for strategy in required
        ),
        preferred_ready_if_all_approved=all(
            projected_map[strategy]
            >= policy.preferred_distinct_market_days_per_strategy
            for strategy in required
        ),
        proposals=tuple(changes),
        overlaps=tuple(overlaps),
        conflicting_pending_facts=any(item.conflict for item in overlaps),
        shared_index_reconciliation_required=(
            sum(bool(change.proposed_additions) for change in changes) > 1
        ),
    )
