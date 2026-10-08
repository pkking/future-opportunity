from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
SELECTION = (
    ROOT
    / "docs/historical-acquisition-plans/cash-stage2-30day-wave-001.json"
)


def test_cash_stage2_selection_is_frozen_before_contract_discovery() -> None:
    raw = json.loads(SELECTION.read_text())
    dates = raw["selected_market_dates"]
    pinned = set(raw["pinned_cash_dates_at_selection"])

    assert raw["strategy"] == "cash-and-carry"
    assert raw["target_pinned_day_count"] == 30
    assert raw["current_pinned_day_count"] == 5
    assert raw["required_new_day_count"] == 25
    assert len(dates) == 25
    assert len(set(dates)) == 25
    assert dates == sorted(dates)
    assert not set(dates) & pinned

    source = raw["source_capacity_evidence"]
    assert source["workflow_run"] == "37714282539"
    assert source["artifact_id"] == "11522419694"
    assert source["artifact_digest"].startswith("sha256:")
    assert source["unique_ready_unpinned_count"] == 172

    assert raw["selection_semantics"].endswith(
        "availability_only_no_economics"
    )
    assert raw["invariants"] == {
        "inspect_economics_before_selection": False,
        "automatic_acquisition": False,
        "automatic_promotion": False,
        "replace_dates_after_outcome_observation": False,
    }
