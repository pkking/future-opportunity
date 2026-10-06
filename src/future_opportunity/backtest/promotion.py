from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.backtest.corpus import (
    HistoricalCorpusEntry,
    load_historical_corpus,
)
from future_opportunity.backtest.fixture import load_funding_history_fixture


SUPPORTED_STRATEGIES = ("funding-carry", "cash-and-carry")


@dataclass(frozen=True, slots=True)
class HistoricalPromotionResult:
    status: str
    entry: HistoricalCorpusEntry
    changed_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"staged", "already_present"}:
            raise ValueError(f"unsupported promotion status: {self.status}")


def promote_historical_compact_fixture(
    source_root: Path,
    *,
    fixture_root: Path,
    index_path: Path,
    source_workflow_run: str | None = None,
    expected_parent_artifact_id: str | None = None,
    expected_parent_artifact_sha256: str | None = None,
    required_strategies: tuple[str, ...] = SUPPORTED_STRATEGIES,
) -> HistoricalPromotionResult:
    """Stage one verified compact fixture into the versioned corpus.

    The operation is idempotent for an already indexed byte-identical fixture.
    Any identity/content collision fails closed.
    """
    source_root = source_root.resolve()
    fixture_root = fixture_root.resolve()
    index_path = index_path.resolve()

    if not source_root.is_dir() or source_root.is_symlink():
        raise ValueError("promotion source must be a real directory")
    if index_path.parent != fixture_root:
        raise ValueError("corpus index must live directly below fixture_root")

    manifest = _load_manifest(source_root)
    entry = _entry_from_manifest(manifest)
    _validate_promotion_provenance(
        manifest,
        source_workflow_run=source_workflow_run,
        expected_parent_artifact_id=expected_parent_artifact_id,
        expected_parent_artifact_sha256=expected_parent_artifact_sha256,
    )
    _validate_source_file_set(source_root, manifest)
    _validate_source_fixture(source_root, entry)

    raw_index = _load_index(index_path)
    existing_entries = tuple(
        _entry_from_index(raw_entry, position)
        for position, raw_entry in enumerate(raw_index["entries"])
    )

    exact = next(
        (
            existing
            for existing in existing_entries
            if existing.dataset_id == entry.dataset_id
            and existing.strategy == entry.strategy
            and existing.entry_market_date == entry.entry_market_date
            and existing.fixture_path == entry.fixture_path
        ),
        None,
    )
    destination = fixture_root / entry.fixture_path
    if exact is not None:
        if not destination.is_dir():
            raise ValueError(
                "indexed historical fixture directory is missing: "
                f"{entry.fixture_path}"
            )
        _assert_directories_identical(source_root, destination, manifest)
        return HistoricalPromotionResult(
            status="already_present",
            entry=entry,
            changed_paths=(),
        )

    _reject_identity_collisions(existing_entries, entry)
    if destination.exists():
        raise ValueError(
            "unindexed historical fixture path already exists: "
            f"{entry.fixture_path}"
        )

    original_index = index_path.read_bytes()
    try:
        shutil.copytree(source_root, destination)
        next_entries = tuple(existing_entries) + (entry,)
        ordered = sorted(
            next_entries,
            key=lambda item: (
                _strategy_rank(item.strategy, required_strategies),
                item.entry_market_date,
                item.dataset_id,
            ),
        )
        index_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "entries": [
                        {
                            "dataset_id": item.dataset_id,
                            "strategy": item.strategy,
                            "entry_market_date": item.entry_market_date,
                            "fixture_path": item.fixture_path,
                        }
                        for item in ordered
                    ],
                },
                indent=2,
            )
            + "\n"
        )

        load_historical_corpus(
            index_path=index_path,
            fixture_root=fixture_root,
            required_strategies=required_strategies,
        )
    except Exception:
        index_path.write_bytes(original_index)
        if destination.exists():
            shutil.rmtree(destination)
        raise

    return HistoricalPromotionResult(
        status="staged",
        entry=entry,
        changed_paths=(
            destination.as_posix(),
            index_path.as_posix(),
        ),
    )


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / "manifest.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError("compact artifact requires a regular manifest.json")
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise TypeError("compact artifact manifest must be an object")
    if raw.get("schema_version") != 1:
        raise ValueError("unsupported compact artifact manifest schema")
    if raw.get("pinning_status") != "commit_ready":
        raise ValueError("compact artifact is not commit_ready")
    return raw


def _entry_from_manifest(manifest: dict[str, Any]) -> HistoricalCorpusEntry:
    dataset_id = _required_manifest_string(manifest, "dataset_id")
    strategy = _required_manifest_string(manifest, "strategy")
    entry_market_date = _required_manifest_string(
        manifest,
        "entry_market_date",
    )
    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"unsupported historical strategy: {strategy}")
    try:
        canonical_date = date.fromisoformat(entry_market_date).isoformat()
    except ValueError as error:
        raise ValueError("historical entry_market_date must use YYYY-MM-DD") from error

    if Path(dataset_id).name != dataset_id or dataset_id in {".", ".."}:
        raise ValueError("historical dataset_id must be a safe directory name")

    return HistoricalCorpusEntry(
        dataset_id=dataset_id,
        strategy=strategy,
        entry_market_date=canonical_date,
        fixture_path=dataset_id,
    )


def _validate_promotion_provenance(
    manifest: dict[str, Any],
    *,
    source_workflow_run: str | None,
    expected_parent_artifact_id: str | None,
    expected_parent_artifact_sha256: str | None,
) -> None:
    derived = manifest.get("derived_from_artifact")
    if not isinstance(derived, dict):
        raise ValueError("compact artifact is missing derived_from_artifact")

    workflow_run = _required_manifest_string(derived, "workflow_run")
    artifact_id = _required_manifest_string(derived, "artifact_id")
    artifact_sha = _normalize_sha256(
        _required_manifest_string(derived, "artifact_zip_sha256")
    )
    if not workflow_run.isdigit():
        raise ValueError("derived workflow_run must be numeric")
    if not artifact_id.isdigit():
        raise ValueError("derived artifact_id must be numeric")

    if source_workflow_run is not None and workflow_run != str(source_workflow_run):
        raise ValueError(
            "promotion source run does not match compact artifact provenance"
        )
    if (
        expected_parent_artifact_id is not None
        and artifact_id != str(expected_parent_artifact_id)
    ):
        raise ValueError(
            "parent artifact id does not match compact artifact provenance"
        )
    if expected_parent_artifact_sha256 is not None:
        expected = _normalize_sha256(expected_parent_artifact_sha256)
        if artifact_sha != expected:
            raise ValueError(
                "parent artifact digest does not match compact artifact provenance"
            )


def _validate_source_file_set(
    source_root: Path,
    manifest: dict[str, Any],
) -> None:
    normalized = manifest.get("normalized")
    if not isinstance(normalized, dict) or not normalized:
        raise ValueError("compact artifact is missing normalized components")

    expected = {"manifest.json"}
    for name, component in normalized.items():
        if not isinstance(component, dict):
            raise ValueError(f"normalized component {name} must be an object")
        raw_path = component.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError(f"normalized component {name} is missing path")
        relative = Path(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(
                f"normalized component {name} path must remain below artifact"
            )
        expected.add(relative.as_posix())

    actual: set[str] = set()
    for path in source_root.rglob("*"):
        relative = path.relative_to(source_root).as_posix()
        if path.is_symlink():
            raise ValueError(
                f"compact artifact must not contain symlink: {relative}"
            )
        if path.is_file():
            actual.add(relative)
        elif path.is_dir():
            continue
        else:
            raise ValueError(
                f"compact artifact contains unsupported file type: {relative}"
            )

    if actual != expected:
        extra = sorted(actual - expected)
        missing = sorted(expected - actual)
        raise ValueError(
            "compact artifact file set differs from manifest; "
            f"extra={extra}, missing={missing}"
        )


def _validate_source_fixture(
    source_root: Path,
    entry: HistoricalCorpusEntry,
) -> None:
    if entry.strategy == "funding-carry":
        loaded = load_funding_history_fixture(source_root)
        if loaded.dataset_id != entry.dataset_id:
            raise ValueError("funding compact dataset_id drifted after load")
        return

    if entry.strategy == "cash-and-carry":
        case = load_cash_and_carry_close_fixture(source_root)
        if case.case_id != entry.dataset_id:
            raise ValueError("cash compact dataset_id drifted after load")
        return

    raise ValueError(f"unsupported historical strategy: {entry.strategy}")


def _load_index(index_path: Path) -> dict[str, Any]:
    if not index_path.is_file() or index_path.is_symlink():
        raise ValueError("historical corpus index must be a regular file")
    raw = json.loads(index_path.read_text())
    if not isinstance(raw, dict):
        raise TypeError("historical corpus index must be an object")
    if raw.get("schema_version") != 1:
        raise ValueError("unsupported historical corpus index schema")
    entries = raw.get("entries")
    if not isinstance(entries, list):
        raise ValueError("historical corpus index requires entries list")
    return raw


def _entry_from_index(
    raw: Any,
    position: int,
) -> HistoricalCorpusEntry:
    if not isinstance(raw, dict):
        raise TypeError(f"historical corpus entry {position} must be an object")
    fields = {}
    for key in (
        "dataset_id",
        "strategy",
        "entry_market_date",
        "fixture_path",
    ):
        value = raw.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(
                f"historical corpus entry {position} requires {key}"
            )
        fields[key] = value
    return HistoricalCorpusEntry(**fields)


def _reject_identity_collisions(
    existing_entries: tuple[HistoricalCorpusEntry, ...],
    incoming: HistoricalCorpusEntry,
) -> None:
    for existing in existing_entries:
        if existing.dataset_id == incoming.dataset_id:
            raise ValueError(
                f"historical dataset_id collision: {incoming.dataset_id}"
            )
        if (
            existing.strategy == incoming.strategy
            and existing.entry_market_date == incoming.entry_market_date
        ):
            raise ValueError(
                "historical strategy/date collision: "
                f"{incoming.strategy} {incoming.entry_market_date}"
            )
        if existing.fixture_path == incoming.fixture_path:
            raise ValueError(
                f"historical fixture_path collision: {incoming.fixture_path}"
            )


def _assert_directories_identical(
    source: Path,
    destination: Path,
    manifest: dict[str, Any],
) -> None:
    _validate_source_file_set(destination, manifest)
    source_files = _relative_file_hashes(source)
    destination_files = _relative_file_hashes(destination)
    if source_files != destination_files:
        raise ValueError(
            "existing indexed historical fixture differs from promoted artifact"
        )


def _relative_file_hashes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result[relative] = digest
    return result


def _strategy_rank(
    strategy: str,
    required_strategies: tuple[str, ...],
) -> int:
    try:
        return required_strategies.index(strategy)
    except ValueError as error:
        raise ValueError(
            f"strategy is not allowed by corpus contract: {strategy}"
        ) from error


def _required_manifest_string(
    raw: dict[str, Any],
    key: str,
) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"compact artifact manifest requires {key}")
    return value


def _normalize_sha256(value: str) -> str:
    normalized = value.removeprefix("sha256:")
    if len(normalized) != 64:
        raise ValueError("artifact SHA-256 must contain 64 hexadecimal characters")
    try:
        int(normalized, 16)
    except ValueError as error:
        raise ValueError("artifact SHA-256 must be hexadecimal") from error
    return normalized.lower()
