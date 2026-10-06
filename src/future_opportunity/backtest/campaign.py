from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from future_opportunity.backtest.corpus import (
    HistoricalCorpus,
    load_historical_corpus,
)
from future_opportunity.backtest.promotion import (
    SUPPORTED_STRATEGIES,
    HistoricalPromotionResult,
    promote_historical_compact_fixture,
)


_SAFE_CAMPAIGN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SAFE_ARTIFACT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True, slots=True)
class HistoricalCampaignArtifactRef:
    source_workflow_run: str
    compact_artifact_name: str

    def __post_init__(self) -> None:
        if not self.source_workflow_run.isdigit():
            raise ValueError("campaign source_workflow_run must be numeric")
        if _SAFE_ARTIFACT_NAME.fullmatch(self.compact_artifact_name) is None:
            raise ValueError(
                "campaign compact_artifact_name must be a safe artifact name"
            )


@dataclass(frozen=True, slots=True)
class HistoricalCampaignManifest:
    schema_version: int
    campaign_id: str
    items: tuple[HistoricalCampaignArtifactRef, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported historical campaign schema")
        if _SAFE_CAMPAIGN_ID.fullmatch(self.campaign_id) is None:
            raise ValueError("historical campaign_id must be a safe identifier")
        if not self.items:
            raise ValueError("historical campaign requires at least one item")


@dataclass(frozen=True, slots=True)
class ResolvedHistoricalCampaignItem:
    source_root: Path
    source_workflow_run: str
    compact_artifact_name: str
    parent_artifact_id: str
    parent_artifact_sha256: str

    def __post_init__(self) -> None:
        HistoricalCampaignArtifactRef(
            source_workflow_run=self.source_workflow_run,
            compact_artifact_name=self.compact_artifact_name,
        )
        if not self.parent_artifact_id.isdigit():
            raise ValueError("campaign parent_artifact_id must be numeric")


@dataclass(frozen=True, slots=True)
class HistoricalCampaignResult:
    status: str
    items: tuple[HistoricalPromotionResult, ...]
    entry_days_by_strategy: tuple[tuple[str, tuple[str, ...]], ...]

    def __post_init__(self) -> None:
        if self.status not in {"staged", "already_present"}:
            raise ValueError(f"unsupported campaign status: {self.status}")

    def counts(self) -> dict[str, int]:
        return {
            strategy: len(days)
            for strategy, days in self.entry_days_by_strategy
        }


def load_historical_campaign_manifest(
    path: Path,
    *,
    max_items: int = 31,
) -> HistoricalCampaignManifest:
    raw = json.loads(path.read_text())
    return parse_historical_campaign_manifest(raw, max_items=max_items)


def parse_historical_campaign_manifest(
    raw: Any,
    *,
    max_items: int = 31,
) -> HistoricalCampaignManifest:
    if not isinstance(raw, dict):
        raise TypeError("historical campaign manifest must be an object")
    if max_items <= 0:
        raise ValueError("historical campaign max_items must be positive")
    expected_keys = {"schema_version", "campaign_id", "items"}
    if set(raw) != expected_keys:
        raise ValueError(
            "historical campaign manifest fields differ from schema"
        )

    schema_version = raw.get("schema_version")
    campaign_id = raw.get("campaign_id")
    raw_items = raw.get("items")
    if not isinstance(schema_version, int):
        raise TypeError("historical campaign schema_version must be integer")
    if not isinstance(campaign_id, str):
        raise TypeError("historical campaign campaign_id must be string")
    if not isinstance(raw_items, list):
        raise TypeError("historical campaign items must be a list")
    if len(raw_items) > max_items:
        raise ValueError(
            f"historical campaign contains {len(raw_items)} items; "
            f"maximum is {max_items}"
        )

    items: list[HistoricalCampaignArtifactRef] = []
    seen_pairs: set[tuple[str, str]] = set()
    seen_names: set[str] = set()
    for position, item in enumerate(raw_items):
        if not isinstance(item, dict):
            raise TypeError(
                f"historical campaign item {position} must be an object"
            )
        if set(item) != {
            "source_workflow_run",
            "compact_artifact_name",
        }:
            raise ValueError(
                f"historical campaign item {position} fields differ from schema"
            )
        run = item.get("source_workflow_run")
        name = item.get("compact_artifact_name")
        if not isinstance(run, str) or not isinstance(name, str):
            raise TypeError(
                f"historical campaign item {position} fields must be strings"
            )
        ref = HistoricalCampaignArtifactRef(
            source_workflow_run=run,
            compact_artifact_name=name,
        )
        pair = (run, name)
        if pair in seen_pairs:
            raise ValueError(
                f"duplicate historical campaign source pair at item {position}"
            )
        if name in seen_names:
            raise ValueError(
                f"duplicate historical campaign compact artifact name: {name}"
            )
        seen_pairs.add(pair)
        seen_names.add(name)
        items.append(ref)

    return HistoricalCampaignManifest(
        schema_version=schema_version,
        campaign_id=campaign_id,
        items=tuple(items),
    )


def promote_historical_campaign(
    items: tuple[ResolvedHistoricalCampaignItem, ...],
    *,
    fixture_root: Path,
    index_path: Path,
    required_strategies: tuple[str, ...] = SUPPORTED_STRATEGIES,
) -> HistoricalCampaignResult:
    if not items:
        raise ValueError("resolved historical campaign requires at least one item")

    source_pairs: set[tuple[str, str]] = set()
    artifact_names: set[str] = set()
    source_roots: set[Path] = set()
    for item in items:
        pair = (item.source_workflow_run, item.compact_artifact_name)
        if pair in source_pairs:
            raise ValueError("resolved campaign contains duplicate source pair")
        if item.compact_artifact_name in artifact_names:
            raise ValueError(
                "resolved campaign contains duplicate compact artifact name"
            )
        root = item.source_root.resolve()
        if root in source_roots:
            raise ValueError("resolved campaign contains duplicate source root")
        source_pairs.add(pair)
        artifact_names.add(item.compact_artifact_name)
        source_roots.add(root)

    fixture_root = fixture_root.resolve()
    index_path = index_path.resolve()
    original_index = index_path.read_bytes()
    staged_directories: list[Path] = []
    results: list[HistoricalPromotionResult] = []

    try:
        for item in items:
            result = promote_historical_compact_fixture(
                item.source_root,
                fixture_root=fixture_root,
                index_path=index_path,
                source_workflow_run=item.source_workflow_run,
                expected_parent_artifact_id=item.parent_artifact_id,
                expected_parent_artifact_sha256=item.parent_artifact_sha256,
                required_strategies=required_strategies,
            )
            results.append(result)
            if result.status == "staged":
                staged_directories.append(
                    fixture_root / result.entry.fixture_path
                )

        corpus = load_historical_corpus(
            index_path=index_path,
            fixture_root=fixture_root,
            required_strategies=required_strategies,
        )
    except Exception:
        index_path.write_bytes(original_index)
        for path in reversed(staged_directories):
            if path.exists():
                shutil.rmtree(path)
        if json.loads(original_index)["entries"]:
            load_historical_corpus(
                index_path=index_path,
                fixture_root=fixture_root,
                required_strategies=required_strategies,
            )
        raise

    return HistoricalCampaignResult(
        status=(
            "staged"
            if any(item.status == "staged" for item in results)
            else "already_present"
        ),
        items=tuple(results),
        entry_days_by_strategy=_entry_days(
            corpus,
            required_strategies=required_strategies,
        ),
    )


def _entry_days(
    corpus: HistoricalCorpus,
    *,
    required_strategies: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    grouped = corpus.entry_days_by_strategy()
    return tuple(
        (strategy, tuple(grouped.get(strategy, ())))
        for strategy in required_strategies
    )
