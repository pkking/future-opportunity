from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from future_opportunity.backtest.campaign import (
    HistoricalCampaignArtifactRef,
    HistoricalCampaignManifest,
    parse_historical_campaign_manifest,
)
from future_opportunity.backtest.corpus import (
    HistoricalCorpus,
    HistoricalCorpusEntry,
)
from future_opportunity.backtest.historical_policy import (
    HistoricalAcceptancePolicy,
)


@dataclass(frozen=True, slots=True)
class VerifiedHistoricalCandidate:
    source_workflow_run: str
    compact_artifact_name: str
    entry: HistoricalCorpusEntry

    def __post_init__(self) -> None:
        HistoricalCampaignArtifactRef(
            source_workflow_run=self.source_workflow_run,
            compact_artifact_name=self.compact_artifact_name,
        )
        if Path(self.entry.dataset_id).name != self.entry.dataset_id:
            raise ValueError("planner dataset_id must be a single directory")


@dataclass(frozen=True, slots=True)
class HistoricalCampaignPlan:
    waves: tuple[HistoricalCampaignManifest, ...]
    selected: tuple[VerifiedHistoricalCandidate, ...]
    excluded_pinned: tuple[VerifiedHistoricalCandidate, ...]
    pinned_counts: tuple[tuple[str, int], ...]
    projected_counts: tuple[tuple[str, int], ...]
    minimum_ready_now: bool
    minimum_ready_if_merged: bool
    preferred_ready_now: bool
    preferred_ready_if_merged: bool


def plan_historical_campaigns(
    candidates: tuple[VerifiedHistoricalCandidate, ...],
    *,
    corpus: HistoricalCorpus,
    policy: HistoricalAcceptancePolicy,
    campaign_prefix: str,
    max_items_per_wave: int = 31,
) -> HistoricalCampaignPlan:
    """Plan review-only campaigns; no corpus files are modified."""
    if not 1 <= max_items_per_wave <= 31:
        raise ValueError("campaign wave size must be within 1..31")
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", campaign_prefix) is None:
        raise ValueError("campaign_prefix must be a safe identifier")

    required = policy.required_strategies
    pinned_date = {
        (entry.strategy, entry.entry_market_date): entry
        for entry in corpus.entries
    }
    seen_pairs: set[tuple[str, str]] = set()
    seen_dates: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()
    selected: list[VerifiedHistoricalCandidate] = []
    excluded: list[VerifiedHistoricalCandidate] = []

    for candidate in candidates:
        pair = (
            candidate.source_workflow_run,
            candidate.compact_artifact_name,
        )
        date_key = (
            candidate.entry.strategy,
            candidate.entry.entry_market_date,
        )
        dataset_id = candidate.entry.dataset_id
        if candidate.entry.strategy not in required:
            raise ValueError(
                f"campaign candidate has unsupported strategy: "
                f"{candidate.entry.strategy}"
            )
        if pair in seen_pairs:
            raise ValueError(f"duplicate candidate source run/artifact: {pair}")
        if date_key in seen_dates:
            raise ValueError(
                f"duplicate candidate strategy/date: {date_key}"
            )
        if dataset_id in seen_ids:
            raise ValueError(f"duplicate candidate dataset_id: {dataset_id}")
        seen_pairs.add(pair)
        seen_dates.add(date_key)
        seen_ids.add(dataset_id)

        pinned = pinned_date.get(date_key)
        if pinned is not None:
            if pinned.dataset_id != dataset_id:
                raise ValueError(
                    "candidate conflicts with pinned strategy/date: "
                    f"{candidate.entry.strategy} "
                    f"{candidate.entry.entry_market_date}"
                )
            excluded.append(candidate)
        else:
            if any(entry.dataset_id == dataset_id for entry in corpus.entries):
                raise ValueError(
                    f"candidate collides with pinned dataset_id: {dataset_id}"
                )
            selected.append(candidate)

    order = {strategy: n for n, strategy in enumerate(required)}
    selected.sort(
        key=lambda item: (
            order[item.entry.strategy],
            item.entry.entry_market_date,
            item.entry.dataset_id,
        )
    )
    excluded.sort(
        key=lambda item: (
            order[item.entry.strategy],
            item.entry.entry_market_date,
            item.entry.dataset_id,
        )
    )

    waves: list[HistoricalCampaignManifest] = []
    for offset in range(0, len(selected), max_items_per_wave):
        batch = selected[offset : offset + max_items_per_wave]
        wave_id = f"{campaign_prefix}-wave-{len(waves) + 1:03d}"
        manifest = parse_historical_campaign_manifest(
            {
                "schema_version": 1,
                "campaign_id": wave_id,
                "items": [
                    {
                        "source_workflow_run": item.source_workflow_run,
                        "compact_artifact_name": item.compact_artifact_name,
                    }
                    for item in batch
                ],
            },
            max_items=max_items_per_wave,
        )
        waves.append(manifest)

    pinned_counts = tuple(
        (
            strategy,
            len(
                {
                    entry.entry_market_date
                    for entry in corpus.entries
                    if entry.strategy == strategy
                }
            ),
        )
        for strategy in required
    )
    selected_counts = {
        strategy: sum(
            item.entry.strategy == strategy for item in selected
        )
        for strategy in required
    }
    projected_counts = tuple(
        (strategy, count + selected_counts[strategy])
        for strategy, count in pinned_counts
    )
    pinned_map = dict(pinned_counts)
    projected_map = dict(projected_counts)

    return HistoricalCampaignPlan(
        waves=tuple(waves),
        selected=tuple(selected),
        excluded_pinned=tuple(excluded),
        pinned_counts=pinned_counts,
        projected_counts=projected_counts,
        minimum_ready_now=all(
            pinned_map[strategy]
            >= policy.minimum_distinct_market_days_per_strategy
            for strategy in required
        ),
        minimum_ready_if_merged=all(
            projected_map[strategy]
            >= policy.minimum_distinct_market_days_per_strategy
            for strategy in required
        ),
        preferred_ready_now=all(
            pinned_map[strategy]
            >= policy.preferred_distinct_market_days_per_strategy
            for strategy in required
        ),
        preferred_ready_if_merged=all(
            projected_map[strategy]
            >= policy.preferred_distinct_market_days_per_strategy
            for strategy in required
        ),
    )
