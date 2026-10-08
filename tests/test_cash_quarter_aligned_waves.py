from __future__ import annotations

import json
from pathlib import Path

from future_opportunity.backtest.acquisition import (
    load_historical_acquisition_manifest,
)


ROOT = Path(__file__).parents[1]
PLAN_ROOT = ROOT / "docs/historical-acquisition-plans"
POLICY = PLAN_ROOT / "cash-quarter-aligned-policy-v1.json"
Q1 = PLAN_ROOT / "cash-stage2-q1-wave-001.json"
Q2 = PLAN_ROOT / "cash-stage2-q2-wave-001.json"
FROZEN = PLAN_ROOT / "cash-stage2-30day-wave-001.json"


def _dates(manifest) -> tuple[str, ...]:
    return tuple(case.entry_market_date for case in manifest.cash_cases)


def test_quarter_aligned_waves_exactly_partition_frozen_selection() -> None:
    frozen = json.loads(FROZEN.read_text())["selected_market_dates"]
    q1 = load_historical_acquisition_manifest(Q1)
    q2 = load_historical_acquisition_manifest(Q2)

    assert q1.funding is None
    assert q2.funding is None
    assert len(q1.cash_cases) == 12
    assert len(q2.cash_cases) == 13
    assert list(_dates(q1) + _dates(q2)) == frozen
    assert set(_dates(q1)).isdisjoint(_dates(q2))


def test_q1_wave_uses_approved_march_quarter_contract() -> None:
    manifest = load_historical_acquisition_manifest(Q1)

    assert manifest.cash_selection_provenance is not None
    assert (
        manifest.cash_selection_provenance.selection_kind
        == "pre_registered_availability_sample"
    )
    for case in manifest.cash_cases:
        assert case.future_id == "BTC-USDT-260327"
        assert case.exit_at == "2026-03-26T00:15:00+00:00"
        assert case.expiry_at == "2026-03-27T08:00:00+00:00"
        assert case.entry_at.endswith("T00:15:00+00:00")


def test_q2_wave_uses_approved_june_quarter_contract() -> None:
    manifest = load_historical_acquisition_manifest(Q2)

    assert manifest.cash_selection_provenance is not None
    for case in manifest.cash_cases:
        assert case.future_id == "BTC-USDT-260626"
        assert case.exit_at == "2026-06-25T00:15:00+00:00"
        assert case.expiry_at == "2026-06-26T08:00:00+00:00"
        assert case.entry_at.endswith("T00:15:00+00:00")


def test_approved_policy_matches_wave_manifests() -> None:
    policy = json.loads(POLICY.read_text())
    q1 = load_historical_acquisition_manifest(Q1)
    q2 = load_historical_acquisition_manifest(Q2)

    assert policy["status"] == "approved"
    assert policy["approved_at"] == "2026-10-08"
    assert policy["entry_time_utc"] == "00:15:00"
    assert policy["invariants"]["no_replacement_after_outcome_observation"]
    assert policy["waves"][0]["entry_dates"] == list(_dates(q1))
    assert policy["waves"][1]["entry_dates"] == list(_dates(q2))
