from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.backtest.fixture import load_funding_history_fixture


@dataclass(frozen=True, slots=True)
class HistoricalCorpusEntry:
    dataset_id: str
    strategy: str
    entry_market_date: str
    fixture_path: str


@dataclass(frozen=True, slots=True)
class HistoricalCorpus:
    schema_version: int
    entries: tuple[HistoricalCorpusEntry, ...]

    def entry_days_by_strategy(self) -> dict[str, tuple[str, ...]]:
        grouped: dict[str, list[str]] = {}
        for entry in self.entries:
            grouped.setdefault(entry.strategy, []).append(entry.entry_market_date)
        return {
            strategy: tuple(sorted(days))
            for strategy, days in grouped.items()
        }


def load_historical_corpus(
    *,
    index_path: Path,
    fixture_root: Path,
    required_strategies: tuple[str, ...],
) -> HistoricalCorpus:
    raw = json.loads(index_path.read_text())
    if not isinstance(raw, dict):
        raise TypeError("historical corpus index must be an object")
    if raw.get("schema_version") != 1:
        raise ValueError("unsupported historical corpus index schema")

    raw_entries = raw.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError("historical corpus index requires entries")

    allowed_strategies = set(required_strategies)
    seen_dataset_ids: set[str] = set()
    seen_strategy_dates: set[tuple[str, str]] = set()
    seen_paths: set[str] = set()
    entries: list[HistoricalCorpusEntry] = []

    for position, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            raise TypeError(
                f"historical corpus entry {position} must be an object"
            )
        dataset_id = _required_string(raw_entry, "dataset_id", position)
        strategy = _required_string(raw_entry, "strategy", position)
        entry_market_date = _required_string(
            raw_entry,
            "entry_market_date",
            position,
        )
        fixture_path = _required_string(raw_entry, "fixture_path", position)

        if strategy not in allowed_strategies:
            raise ValueError(
                f"historical corpus entry {position} has unsupported "
                f"strategy: {strategy}"
            )
        try:
            parsed_date = date.fromisoformat(entry_market_date)
        except ValueError as error:
            raise ValueError(
                f"historical corpus entry {position} has invalid "
                "entry_market_date"
            ) from error
        canonical_date = parsed_date.isoformat()

        relative = Path(fixture_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(
                f"historical corpus entry {position} fixture_path "
                "must remain below fixture_root"
            )
        canonical_path = relative.as_posix()

        if dataset_id in seen_dataset_ids:
            raise ValueError(
                f"duplicate historical corpus dataset_id: {dataset_id}"
            )
        strategy_date = (strategy, canonical_date)
        if strategy_date in seen_strategy_dates:
            raise ValueError(
                "duplicate historical corpus strategy/date: "
                f"{strategy} {canonical_date}"
            )
        if canonical_path in seen_paths:
            raise ValueError(
                f"duplicate historical corpus fixture_path: {canonical_path}"
            )

        root = fixture_root / relative
        manifest = _load_manifest(root)
        pinning_status = manifest.get("pinning_status")
        if pinning_status is not None and pinning_status != "commit_ready":
            raise ValueError(
                f"historical corpus fixture is not commit_ready: {canonical_path}"
            )
        if manifest.get("dataset_id") != dataset_id:
            raise ValueError(
                f"historical corpus dataset_id drift for {canonical_path}"
            )
        if manifest.get("strategy") != strategy:
            raise ValueError(
                f"historical corpus strategy drift for {canonical_path}"
            )
        if manifest.get("entry_market_date") != canonical_date:
            raise ValueError(
                f"historical corpus entry date drift for {canonical_path}"
            )

        _validate_strategy_fixture(
            strategy=strategy,
            root=root,
            entry_market_date=canonical_date,
            manifest=manifest,
            dataset_id=dataset_id,
        )

        entries.append(
            HistoricalCorpusEntry(
                dataset_id=dataset_id,
                strategy=strategy,
                entry_market_date=canonical_date,
                fixture_path=canonical_path,
            )
        )
        seen_dataset_ids.add(dataset_id)
        seen_strategy_dates.add(strategy_date)
        seen_paths.add(canonical_path)

    indexed_paths = {entry.fixture_path for entry in entries}
    discovered_paths = _discover_pinned_fixture_paths(fixture_root)
    missing_from_index = sorted(discovered_paths - indexed_paths)
    unknown_in_index = sorted(indexed_paths - discovered_paths)
    if missing_from_index:
        raise ValueError(
            "historical corpus has unindexed pinned fixtures: "
            + ", ".join(missing_from_index)
        )
    if unknown_in_index:
        raise ValueError(
            "historical corpus index references non-pinned fixtures: "
            + ", ".join(unknown_in_index)
        )

    return HistoricalCorpus(
        schema_version=1,
        entries=tuple(entries),
    )


def _validate_strategy_fixture(
    *,
    strategy: str,
    root: Path,
    entry_market_date: str,
    manifest: dict[str, Any],
    dataset_id: str,
) -> None:
    if strategy == "funding-carry":
        fixture = load_funding_history_fixture(root)
        if fixture.dataset_id != dataset_id:
            raise ValueError("funding fixture dataset_id drifted after load")
        if manifest.get("history_date_utc") != entry_market_date:
            raise ValueError(
                "funding fixture history_date_utc differs from entry day"
            )
        return

    if strategy == "cash-and-carry":
        case = load_cash_and_carry_close_fixture(root)
        if case.case_id != dataset_id:
            raise ValueError("cash fixture dataset_id drifted after load")
        sample_times = manifest.get("sample_times")
        if not isinstance(sample_times, dict):
            raise ValueError("cash fixture is missing sample_times")
        raw_entry = sample_times.get("entry")
        if not isinstance(raw_entry, str):
            raise ValueError("cash fixture entry sample is invalid")
        try:
            entry_at = datetime.fromisoformat(raw_entry)
        except ValueError as error:
            raise ValueError("cash fixture entry sample is invalid") from error
        if entry_at.tzinfo is None:
            raise ValueError("cash fixture entry sample must be timezone-aware")
        if entry_at.date().isoformat() != entry_market_date:
            raise ValueError(
                "cash fixture entry sample differs from indexed entry day"
            )
        return

    raise ValueError(f"unsupported historical corpus strategy: {strategy}")


def _discover_pinned_fixture_paths(fixture_root: Path) -> set[str]:
    discovered: set[str] = set()
    for manifest_path in fixture_root.rglob("manifest.json"):
        manifest = json.loads(manifest_path.read_text())
        if not isinstance(manifest, dict):
            raise TypeError(
                f"historical fixture manifest must be an object: "
                f"{manifest_path}"
            )
        if (
            isinstance(manifest.get("strategy"), str)
            and isinstance(manifest.get("entry_market_date"), str)
        ):
            discovered.add(
                manifest_path.parent.relative_to(fixture_root).as_posix()
            )
    return discovered


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise TypeError(f"historical fixture manifest must be an object: {path}")
    return raw


def _required_string(
    raw: dict[str, Any],
    key: str,
    position: int,
) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"historical corpus entry {position} requires {key}"
        )
    return value
