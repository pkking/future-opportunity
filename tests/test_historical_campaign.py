from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from future_opportunity.backtest.campaign import (
    ResolvedHistoricalCampaignItem,
    parse_historical_campaign_manifest,
    promote_historical_campaign,
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


def funding_item(source: Path = FUNDING) -> ResolvedHistoricalCampaignItem:
    return ResolvedHistoricalCampaignItem(
        source_root=source,
        source_workflow_run="37327493270",
        compact_artifact_name="okx-btc-funding-compact-2026-09-02",
        parent_artifact_id="11353260627",
        parent_artifact_sha256=(
            "4eed3e2eac19b19aca29dd4ce76bc3f596d6b09a51c22d587b734825d520af74"
        ),
    )


def cash_item(source: Path = CASH) -> ResolvedHistoricalCampaignItem:
    return ResolvedHistoricalCampaignItem(
        source_root=source,
        source_workflow_run="37327804191",
        compact_artifact_name=(
            "okx-btc-cash-and-carry-compact-BTC-USDT-260626-37327804191"
        ),
        parent_artifact_id="11353125961",
        parent_artifact_sha256=(
            "1d1ca77522befbc4fa2eb27c57fa15c15eb4915db50cf1fc08beb0c6f8fcfa31"
        ),
    )


def test_campaign_manifest_is_versioned_bounded_and_rejects_duplicates() -> None:
    parsed = parse_historical_campaign_manifest(
        {
            "schema_version": 1,
            "campaign_id": "stage1-wave-01",
            "items": [
                {
                    "source_workflow_run": "1",
                    "compact_artifact_name": "funding-a",
                },
                {
                    "source_workflow_run": "2",
                    "compact_artifact_name": "cash-b",
                },
            ],
        }
    )
    assert parsed.campaign_id == "stage1-wave-01"
    assert len(parsed.items) == 2

    with pytest.raises(ValueError, match="duplicate historical campaign source pair"):
        parse_historical_campaign_manifest(
            {
                "schema_version": 1,
                "campaign_id": "duplicate",
                "items": [
                    {
                        "source_workflow_run": "1",
                        "compact_artifact_name": "same",
                    },
                    {
                        "source_workflow_run": "1",
                        "compact_artifact_name": "same",
                    },
                ],
            }
        )

    with pytest.raises(ValueError, match="duplicate historical campaign compact"):
        parse_historical_campaign_manifest(
            {
                "schema_version": 1,
                "campaign_id": "duplicate-name",
                "items": [
                    {
                        "source_workflow_run": "1",
                        "compact_artifact_name": "same",
                    },
                    {
                        "source_workflow_run": "2",
                        "compact_artifact_name": "same",
                    },
                ],
            }
        )

    with pytest.raises(ValueError, match="maximum is 1"):
        parse_historical_campaign_manifest(
            {
                "schema_version": 1,
                "campaign_id": "too-large",
                "items": [
                    {
                        "source_workflow_run": "1",
                        "compact_artifact_name": "a",
                    },
                    {
                        "source_workflow_run": "2",
                        "compact_artifact_name": "b",
                    },
                ],
            },
            max_items=1,
        )


def test_mixed_campaign_is_atomic_and_index_order_ignores_input_order(
    tmp_path: Path,
) -> None:
    fixture_root, index = empty_corpus(tmp_path)

    result = promote_historical_campaign(
        (cash_item(), funding_item()),
        fixture_root=fixture_root,
        index_path=index,
    )

    assert result.status == "staged"
    assert result.counts() == {
        "funding-carry": 1,
        "cash-and-carry": 1,
    }
    raw = json.loads(index.read_text())
    assert [
        (entry["strategy"], entry["entry_market_date"])
        for entry in raw["entries"]
    ] == [
        ("funding-carry", "2026-09-02"),
        ("cash-and-carry", "2026-06-02"),
    ]


def test_campaign_rolls_back_earlier_staged_items_when_later_item_fails(
    tmp_path: Path,
) -> None:
    fixture_root, index = empty_corpus(tmp_path)
    broken_cash = tmp_path / "broken-cash"
    shutil.copytree(CASH, broken_cash)
    manifest_path = broken_cash / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["pinning_status"] = "prepared_unpinned"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    with pytest.raises(ValueError, match="not commit_ready"):
        promote_historical_campaign(
            (funding_item(), cash_item(broken_cash)),
            fixture_root=fixture_root,
            index_path=index,
        )

    assert json.loads(index.read_text())["entries"] == []
    assert not (
        fixture_root
        / "okx-btc-usdt-funding-carry-2026-09-02-v1-target-compact"
    ).exists()


def test_campaign_can_mix_already_present_and_new_then_become_full_noop(
    tmp_path: Path,
) -> None:
    fixture_root, index = empty_corpus(tmp_path)

    first = promote_historical_campaign(
        (funding_item(),),
        fixture_root=fixture_root,
        index_path=index,
    )
    assert first.status == "staged"

    mixed = promote_historical_campaign(
        (funding_item(), cash_item()),
        fixture_root=fixture_root,
        index_path=index,
    )
    assert mixed.status == "staged"
    assert [item.status for item in mixed.items] == [
        "already_present",
        "staged",
    ]

    noop = promote_historical_campaign(
        (cash_item(), funding_item()),
        fixture_root=fixture_root,
        index_path=index,
    )
    assert noop.status == "already_present"
    assert all(item.status == "already_present" for item in noop.items)
    assert noop.counts() == {
        "funding-carry": 1,
        "cash-and-carry": 1,
    }


def test_resolved_campaign_rejects_duplicate_artifact_names(
    tmp_path: Path,
) -> None:
    fixture_root, index = empty_corpus(tmp_path)
    duplicate = ResolvedHistoricalCampaignItem(
        source_root=CASH,
        source_workflow_run="37327804191",
        compact_artifact_name="okx-btc-funding-compact-2026-09-02",
        parent_artifact_id="11353125961",
        parent_artifact_sha256=(
            "1d1ca77522befbc4fa2eb27c57fa15c15eb4915db50cf1fc08beb0c6f8fcfa31"
        ),
    )

    with pytest.raises(ValueError, match="duplicate compact artifact name"):
        promote_historical_campaign(
            (funding_item(), duplicate),
            fixture_root=fixture_root,
            index_path=index,
        )
