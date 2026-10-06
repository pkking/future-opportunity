import json
from pathlib import Path

import pytest

from future_opportunity.backtest.corpus import load_historical_corpus


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests/fixtures/historical"
INDEX = FIXTURES / "corpus-index.json"
STRATEGIES = ("funding-carry", "cash-and-carry")


def test_repository_historical_corpus_is_explicit_and_replayable() -> None:
    corpus = load_historical_corpus(
        index_path=INDEX,
        fixture_root=FIXTURES,
        required_strategies=STRATEGIES,
    )

    raw = json.loads(INDEX.read_text())
    expected_days = {
        strategy: tuple(
            sorted(
                entry["entry_market_date"]
                for entry in raw["entries"]
                if entry["strategy"] == strategy
            )
        )
        for strategy in STRATEGIES
    }

    assert len(corpus.entries) == len(raw["entries"])
    assert corpus.entry_days_by_strategy() == expected_days


def test_corpus_rejects_duplicate_strategy_date(tmp_path: Path) -> None:
    raw = json.loads(INDEX.read_text())
    duplicate = dict(raw["entries"][0])
    duplicate["dataset_id"] = duplicate["dataset_id"] + "-duplicate"
    duplicate["fixture_path"] = raw["entries"][1]["fixture_path"]
    raw["entries"].append(duplicate)
    index = tmp_path / "corpus-index.json"
    index.write_text(json.dumps(raw))

    with pytest.raises(ValueError, match="duplicate historical corpus strategy/date"):
        load_historical_corpus(
            index_path=index,
            fixture_root=FIXTURES,
            required_strategies=STRATEGIES,
        )


def test_corpus_rejects_unindexed_pinned_fixture(tmp_path: Path) -> None:
    raw = json.loads(INDEX.read_text())
    raw["entries"] = raw["entries"][:1]
    index = tmp_path / "corpus-index.json"
    index.write_text(json.dumps(raw))

    with pytest.raises(ValueError, match="unindexed pinned fixtures"):
        load_historical_corpus(
            index_path=index,
            fixture_root=FIXTURES,
            required_strategies=STRATEGIES,
        )


def test_corpus_rejects_manifest_index_drift(tmp_path: Path) -> None:
    raw = json.loads(INDEX.read_text())
    raw["entries"][0]["entry_market_date"] = "2026-09-02"
    index = tmp_path / "corpus-index.json"
    index.write_text(json.dumps(raw))

    with pytest.raises(ValueError, match="entry date drift"):
        load_historical_corpus(
            index_path=index,
            fixture_root=FIXTURES,
            required_strategies=STRATEGIES,
        )


def test_corpus_rejects_unfinalized_compact_fixture(tmp_path: Path) -> None:
    raw = json.loads(INDEX.read_text())
    fixture_path = FIXTURES / raw["entries"][0]["fixture_path"]
    copied_root = tmp_path / "fixtures"
    copied_root.mkdir()
    target = copied_root / raw["entries"][0]["fixture_path"]

    import shutil

    shutil.copytree(fixture_path, target)
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["pinning_status"] = "prepared_unpinned"
    manifest_path.write_text(json.dumps(manifest))

    index = copied_root / "corpus-index.json"
    index.write_text(json.dumps({"schema_version": 1, "entries": [raw["entries"][0]]}))

    with pytest.raises(ValueError, match="not commit_ready"):
        load_historical_corpus(
            index_path=index,
            fixture_root=copied_root,
            required_strategies=STRATEGIES,
        )
