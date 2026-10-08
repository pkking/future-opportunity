from __future__ import annotations

import pytest

from future_opportunity.backtest.stratified_evidence_selection import (
    plan_stratified_evidence_days,
)


def test_outcome_blind_regime_selection_is_deterministic() -> None:
    days = {
        "2026-01-01": "low",
        "2026-01-02": "low",
        "2026-01-03": "high",
        "2026-01-04": "high",
        "2026-01-05": None,
    }
    def run():
        return plan_stratified_evidence_days(
            days, strata=("low", "high"), quota_per_stratum=1,
            seed="registered-001",
        )
    assert run() == run()
    assert all(len(v) == 1 for v in run()["selected_by_stratum"].values())
    assert run()["unassessed_label_dates"] == ["2026-01-05"]
    assert run()["observed_population_count"] == 5


def test_unavailable_source_never_replaced_with_outcome_case() -> None:
    days = {"2026-01-01": "low", "2026-01-02": "high"}
    result = plan_stratified_evidence_days(
        days, strata=("low", "high"), quota_per_stratum=1,
        seed="registered-002", unavailable_dates=("2026-01-01",),
    )
    assert result["selected_by_stratum"]["low"] == []
    assert result["shortfall_by_stratum"]["low"] == 1
    assert result["capacity_sufficient"] is False
    assert result["unavailable_dates"] == ["2026-01-01"]


def test_missing_label_is_not_counted_as_zero_opportunities() -> None:
    result = plan_stratified_evidence_days(
        {"2026-02-01": None},
        strata=("quiet",), quota_per_stratum=1, seed="registered-003",
    )
    assert result["unassessed_label_dates"] == ["2026-02-01"]
    assert result["stratum_population_counts"]["quiet"] == 0
    assert result["shortfall_by_stratum"]["quiet"] == 1


@pytest.mark.parametrize(
    "labels,quota,seed,unknown,missing",
    [
        (("low", "low"), 1, "seed", {}, ()),
        (("low",), 0, "seed", {}, ()),
        (("low",), 1, "", {}, ()),
        (("low",), 1, "seed", {"2026-01-01": "high"}, ()),
        (("low",), 1, "seed", {}, ("2026-01-01",)),
    ],
)
def test_invalid_selection_request_fails_closed(
    labels, quota, seed, unknown, missing,
) -> None:
    with pytest.raises(ValueError):
        plan_stratified_evidence_days(
            unknown, strata=labels, quota_per_stratum=quota,
            seed=seed, unavailable_dates=missing,
        )
