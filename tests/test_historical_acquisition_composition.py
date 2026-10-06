from __future__ import annotations

import pytest

from future_opportunity.backtest.acquisition import (
    acquisition_dispatch_payload,
)
from future_opportunity.backtest.acquisition_composition import (
    acquisition_cash_cases_from_plan,
    compose_historical_acquisition,
)


def case_plan(
    *,
    selected: bool = True,
) -> dict[str, object]:
    cash_cases = (
        [
            {
                "entry_at": "2026-06-03T00:15:00+00:00",
                "entry_market_date": "2026-06-03",
                "exit_at": "2026-06-25T00:15:00+00:00",
                "expiry_at": "2026-06-26T08:00:00+00:00",
                "future_id": "BTC-USDT-260626",
            }
        ]
        if selected
        else []
    )
    excluded = (
        []
        if selected
        else [
            {
                "market_date": "2026-06-03",
                "reason": "no_unique_future_chain_archive",
                "discovered_future_id": None,
            }
        ]
    )
    return {
        "schema_version": 1,
        "evidence_type": "read_only_cash_acquisition_case_plan",
        "template": {
            "future_id": "BTC-USDT-260626",
            "expiry_at": "2026-06-26T08:00:00+00:00",
            "exit_at": "2026-06-25T00:15:00+00:00",
            "entry_time_utc": "00:15:00",
        },
        "selected_count": len(cash_cases),
        "excluded_count": len(excluded),
        "cash_cases": cash_cases,
        "excluded": excluded,
        "source_reports": ["000/report.json"],
        "note": "read-only",
    }


def test_composer_supports_funding_only() -> None:
    manifest = compose_historical_acquisition(
        acquisition_id="funding-only",
        planner_campaign_prefix="funding-review",
        funding_start_date="2026-09-04",
        funding_end_date="2026-09-05",
    )

    assert manifest.total_items == 2
    assert manifest.funding is not None
    assert manifest.cash_cases == ()
    assert acquisition_dispatch_payload(manifest) == {
        "schema_version": 1,
        "acquisition_id": "funding-only",
        "planner_campaign_prefix": "funding-review",
        "funding": {
            "start_date": "2026-09-04",
            "end_date": "2026-09-05",
        },
        "cash_cases": [],
    }


def test_composer_supports_cash_only_and_strips_reporting_fields() -> None:
    manifest = compose_historical_acquisition(
        acquisition_id="cash-only",
        planner_campaign_prefix="cash-review",
        cash_case_plan=case_plan(),
    )

    assert manifest.total_items == 1
    assert manifest.funding is None
    payload = acquisition_dispatch_payload(manifest)
    assert payload["cash_cases"] == [
        {
            "entry_at": "2026-06-03T00:15:00+00:00",
            "exit_at": "2026-06-25T00:15:00+00:00",
            "future_id": "BTC-USDT-260626",
            "expiry_at": "2026-06-26T08:00:00+00:00",
        }
    ]
    assert "entry_market_date" not in payload["cash_cases"][0]


def test_composer_supports_mixed_and_reuses_total_item_cap() -> None:
    manifest = compose_historical_acquisition(
        acquisition_id="mixed",
        planner_campaign_prefix="mixed-review",
        funding_start_date="2026-09-04",
        funding_end_date="2026-09-05",
        cash_case_plan=case_plan(),
    )
    assert manifest.total_items == 3

    with pytest.raises(ValueError, match="maximum is 2"):
        compose_historical_acquisition(
            acquisition_id="overflow",
            planner_campaign_prefix="overflow-review",
            funding_start_date="2026-09-04",
            funding_end_date="2026-09-05",
            cash_case_plan=case_plan(),
            max_total_items=2,
        )


def test_composer_requires_complete_funding_range_and_nonempty_effective_input() -> None:
    with pytest.raises(ValueError, match="must be supplied together"):
        compose_historical_acquisition(
            acquisition_id="bad-funding",
            planner_campaign_prefix="bad-review",
            funding_start_date="2026-09-04",
        )

    with pytest.raises(ValueError, match="at least one Funding day or Cash case"):
        compose_historical_acquisition(
            acquisition_id="empty",
            planner_campaign_prefix="empty-review",
            cash_case_plan=case_plan(selected=False),
        )


def test_case_plan_validation_rejects_schema_count_and_template_drift() -> None:
    wrong_type = case_plan()
    wrong_type["evidence_type"] = "other"
    with pytest.raises(ValueError, match="unexpected Cash case-plan evidence_type"):
        acquisition_cash_cases_from_plan(wrong_type)

    wrong_count = case_plan()
    wrong_count["selected_count"] = 2
    with pytest.raises(ValueError, match="selected_count"):
        acquisition_cash_cases_from_plan(wrong_count)

    wrong_template = case_plan()
    wrong_template["cash_cases"][0]["future_id"] = "BTC-USDT-260925"
    with pytest.raises(ValueError, match="future_id differs from template"):
        acquisition_cash_cases_from_plan(wrong_template)

    wrong_excluded = case_plan(selected=False)
    wrong_excluded["excluded"][0]["extra"] = True
    with pytest.raises(ValueError, match="excluded 0 fields differ"):
        acquisition_cash_cases_from_plan(wrong_excluded)


def test_case_plan_validation_requires_source_evidence_and_entry_time_consistency() -> None:
    no_source = case_plan()
    no_source["source_reports"] = []
    with pytest.raises(ValueError, match="source_reports"):
        acquisition_cash_cases_from_plan(no_source)

    drifted_time = case_plan()
    drifted_time["cash_cases"][0]["entry_at"] = "2026-06-03T00:30:00+00:00"
    with pytest.raises(ValueError, match="entry time differs from template"):
        acquisition_cash_cases_from_plan(drifted_time)
