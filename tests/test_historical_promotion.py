from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from future_opportunity.backtest.promotion import (
    promote_historical_compact_fixture,
)


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests/fixtures/historical"
FUNDING = (
    FIXTURES
    / "okx-btc-usdt-funding-carry-2026-09-02-v1-target-compact"
)
CASH = (
    FIXTURES
    / "okx-btc-usdt-cash-and-carry-2026-06-02-BTC-USDT-260626-v1-target-compact"
)


def empty_corpus(tmp_path: Path) -> tuple[Path, Path]:
    fixture_root = tmp_path / "historical"
    fixture_root.mkdir()
    index = fixture_root / "corpus-index.json"
    index.write_text(
        json.dumps({"schema_version": 1, "entries": []}, indent=2) + "\n"
    )
    return fixture_root, index


def test_promotes_funding_fixture_and_is_idempotent(tmp_path: Path) -> None:
    fixture_root, index = empty_corpus(tmp_path)

    first = promote_historical_compact_fixture(
        FUNDING,
        fixture_root=fixture_root,
        index_path=index,
        source_workflow_run="37327493270",
        expected_parent_artifact_id="11353260627",
        expected_parent_artifact_sha256=(
            "4eed3e2eac19b19aca29dd4ce76bc3f596d6b09a51c22d587b734825d520af74"
        ),
    )

    assert first.status == "staged"
    assert first.entry.strategy == "funding-carry"
    assert (fixture_root / first.entry.fixture_path / "manifest.json").is_file()

    second = promote_historical_compact_fixture(
        FUNDING,
        fixture_root=fixture_root,
        index_path=index,
        source_workflow_run="37327493270",
    )

    assert second.status == "already_present"
    assert second.changed_paths == ()
    raw = json.loads(index.read_text())
    assert len(raw["entries"]) == 1


def test_promotes_cash_fixture_and_index_order_is_deterministic(
    tmp_path: Path,
) -> None:
    fixture_root, index = empty_corpus(tmp_path)

    cash_result = promote_historical_compact_fixture(
        CASH,
        fixture_root=fixture_root,
        index_path=index,
        source_workflow_run="37327804191",
    )
    funding_result = promote_historical_compact_fixture(
        FUNDING,
        fixture_root=fixture_root,
        index_path=index,
        source_workflow_run="37327493270",
    )

    assert cash_result.status == "staged"
    assert funding_result.status == "staged"

    raw = json.loads(index.read_text())
    assert [
        (entry["strategy"], entry["entry_market_date"])
        for entry in raw["entries"]
    ] == [
        ("funding-carry", "2026-09-02"),
        ("cash-and-carry", "2026-06-02"),
    ]


def test_rejects_same_strategy_date_with_different_dataset(
    tmp_path: Path,
) -> None:
    fixture_root, index = empty_corpus(tmp_path)
    promote_historical_compact_fixture(
        FUNDING,
        fixture_root=fixture_root,
        index_path=index,
    )

    conflicting = tmp_path / "conflicting"
    shutil.copytree(FUNDING, conflicting)
    manifest_path = conflicting / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["dataset_id"] = manifest["dataset_id"] + "-different"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    with pytest.raises(ValueError, match="strategy/date collision"):
        promote_historical_compact_fixture(
            conflicting,
            fixture_root=fixture_root,
            index_path=index,
        )


def test_repromotion_rejects_divergent_existing_fixture(
    tmp_path: Path,
) -> None:
    fixture_root, index = empty_corpus(tmp_path)
    result = promote_historical_compact_fixture(
        FUNDING,
        fixture_root=fixture_root,
        index_path=index,
    )
    destination = fixture_root / result.entry.fixture_path
    book = destination / "btc-usdt-spot-books.jsonl"
    book.write_text(book.read_text() + "\n")

    with pytest.raises(ValueError, match="differs from promoted artifact"):
        promote_historical_compact_fixture(
            FUNDING,
            fixture_root=fixture_root,
            index_path=index,
        )


def test_rejects_source_run_provenance_mismatch(tmp_path: Path) -> None:
    fixture_root, index = empty_corpus(tmp_path)

    with pytest.raises(ValueError, match="source run"):
        promote_historical_compact_fixture(
            CASH,
            fixture_root=fixture_root,
            index_path=index,
            source_workflow_run="999999",
        )


def test_rejects_extra_unmanifested_file(tmp_path: Path) -> None:
    fixture_root, index = empty_corpus(tmp_path)
    incoming = tmp_path / "incoming"
    shutil.copytree(CASH, incoming)
    (incoming / "unexpected.txt").write_text("not part of compact evidence")

    with pytest.raises(ValueError, match="file set differs"):
        promote_historical_compact_fixture(
            incoming,
            fixture_root=fixture_root,
            index_path=index,
        )
