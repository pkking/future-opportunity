from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from future_opportunity.backtest.cash_prior_quarter_selection import (
    validate_cash_prior_quarter_preregistration,
)


ROOT = Path(__file__).parents[1]
SELECTION = ROOT / "docs/historical-acquisition-plans/cash-2025-q3q4-24day-preregistration-v1.json"
INDEX = ROOT / "tests/fixtures/historical/corpus-index.json"


def input_selection() -> dict:
    return json.loads(SELECTION.read_text())


def pinned_dates() -> list[str]:
    return [
        entry["entry_market_date"]
        for entry in json.loads(INDEX.read_text())["entries"]
        if entry["strategy"] == "cash-and-carry"
    ]


def test_two_expiry_cohorts_are_deterministically_frozen() -> None:
    raw = input_selection()
    result = validate_cash_prior_quarter_preregistration(
        raw, pinned_cash_market_dates=pinned_dates(),
    )
    assert result == validate_cash_prior_quarter_preregistration(
        copy.deepcopy(raw), pinned_cash_market_dates=pinned_dates()
    )
    assert result["selected_market_date_count"] == 24
    assert len(set(result["selected_market_dates"])) == 24
    assert not set(result["selected_market_dates"]) & set(pinned_dates())
    assert len(result["quarters"]) == 2
    assert result["quarters"][0]["population_size"] == 87
    assert result["quarters"][1]["population_size"] == 90
    assert all(len(item["selected_market_dates"]) == 12 for item in result["quarters"])
    assert result["quarters"][0]["selected_market_dates"] == [
        "2025-07-04", "2025-07-11", "2025-07-19", "2025-07-26",
        "2025-08-02", "2025-08-09", "2025-08-17", "2025-08-24",
        "2025-08-31", "2025-09-07", "2025-09-15", "2025-09-22",
    ]
    assert result["quarters"][1]["selected_market_dates"] == [
        "2025-09-30", "2025-10-08", "2025-10-15", "2025-10-23",
        "2025-10-30", "2025-11-07", "2025-11-14", "2025-11-22",
        "2025-11-29", "2025-12-07", "2025-12-14", "2025-12-22",
    ]
    assert all(len(item["selection_evidence_sha256"]) == 64 for item in result["quarters"])
    assert result["economics_inspected_for_selection"] is False
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False


@pytest.mark.parametrize("quarter_index", [0, 1])
def test_any_selected_date_drift_is_rejected(quarter_index: int) -> None:
    raw = input_selection()
    raw["quarters"][quarter_index]["selected_market_dates"][0] = "2025-08-01"
    with pytest.raises(ValueError, match="deterministic replay"):
        validate_cash_prior_quarter_preregistration(
            raw, pinned_cash_market_dates=pinned_dates(),
        )


def test_source_digest_or_quarterly_contract_tampering_fails() -> None:
    raw = input_selection()
    raw["source_capacity_evidence"]["artifact_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="source capacity"):
        validate_cash_prior_quarter_preregistration(
            raw, pinned_cash_market_dates=pinned_dates(),
        )
    raw = input_selection()
    raw["quarters"][0]["future_id"] = "BTC-USDT-251226"
    with pytest.raises(ValueError, match="frozen design"):
        validate_cash_prior_quarter_preregistration(
            raw, pinned_cash_market_dates=pinned_dates(),
        )


def test_expiry_quarter_change_and_existing_date_overlap_fail() -> None:
    raw = input_selection()
    raw["quarters"][0]["exit_at"] = "2025-09-27T00:15:00+00:00"
    with pytest.raises(ValueError, match="frozen design"):
        validate_cash_prior_quarter_preregistration(
            raw, pinned_cash_market_dates=pinned_dates(),
        )
    raw = input_selection()
    with pytest.raises(ValueError, match="overlaps pinned"):
        validate_cash_prior_quarter_preregistration(
            raw, pinned_cash_market_dates=pinned_dates() + ["2025-07-04"],
        )


def test_economic_review_flags_cannot_be_switched_on() -> None:
    raw = input_selection()
    raw["invariants"]["automatic_promotion"] = True
    with pytest.raises(ValueError, match="governance invariants"):
        validate_cash_prior_quarter_preregistration(
            raw, pinned_cash_market_dates=pinned_dates(),
        )


def test_workflow_is_only_a_selection_evidence_control() -> None:
    wf = (ROOT / ".github/workflows/freeze-cash-2025-quarter-selection.yml").read_text()
    assert "workflow_dispatch:" in wf
    assert "cash-2025-quarter-selection-control" in wf
    assert "scripts/freeze_cash_2025_quarter_selection.py" in wf
    assert "promote-historical" not in wf
    assert "acquire-historical" not in wf
