from __future__ import annotations

import pytest

from future_opportunity.backtest.cash_case_planning import (
    CashAcquisitionTemplate,
    parse_cash_discovery_report,
    plan_cash_acquisition_cases,
)


def discovered(
    market_date: str,
    future_id: str = "BTC-USDT-260626",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "market_date": market_date,
        "status": "future_discovered",
        "future": {
            "instrument_id": future_id,
            "delivery_evidence": {"status": "unassessed"},
        },
    }


def missing(market_date: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "market_date": market_date,
        "status": "no_unique_future_chain_archive",
        "candidate_count": 0,
    }


def template() -> CashAcquisitionTemplate:
    return CashAcquisitionTemplate(
        future_id="BTC-USDT-260626",
        expiry_at="2026-06-26T08:00:00+00:00",
        exit_at="2026-06-25T00:15:00+00:00",
        entry_time_utc="00:15:00",
    )


def test_planner_selects_matching_dates_and_reports_exclusions() -> None:
    plan = plan_cash_acquisition_cases(
        (
            discovered("2026-06-04"),
            discovered("2026-06-05", "BTC-USDT-260925"),
            missing("2026-06-06"),
        ),
        template=template(),
    )

    assert plan.selected_count == 1
    assert plan.selected[0].entry_at == "2026-06-04T00:15:00+00:00"
    assert plan.selected[0].exit_at == "2026-06-25T00:15:00+00:00"
    assert plan.selected[0].future_id == "BTC-USDT-260626"
    assert plan.excluded_count == 2
    assert [
        (item.market_date, item.reason, item.discovered_future_id)
        for item in plan.excluded
    ] == [
        ("2026-06-05", "future_id_mismatch", "BTC-USDT-260925"),
        ("2026-06-06", "no_unique_future_chain_archive", None),
    ]


def test_planner_sorts_dates_and_excludes_entries_after_explicit_exit() -> None:
    plan = plan_cash_acquisition_cases(
        (
            discovered("2026-06-25"),
            discovered("2026-06-03"),
            discovered("2026-06-04"),
        ),
        template=template(),
    )

    assert [case.entry_market_date for case in plan.selected] == [
        "2026-06-03",
        "2026-06-04",
    ]
    assert [(item.market_date, item.reason) for item in plan.excluded] == [
        ("2026-06-25", "entry_not_before_explicit_exit"),
    ]


def test_discovery_parser_rejects_schema_status_and_future_drift() -> None:
    with pytest.raises(ValueError, match="unsupported Cash discovery report schema"):
        parse_cash_discovery_report(
            {
                "schema_version": 2,
                "market_date": "2026-06-04",
                "status": "future_discovered",
            }
        )

    with pytest.raises(ValueError, match="unsupported Cash discovery status"):
        parse_cash_discovery_report(
            {
                "schema_version": 1,
                "market_date": "2026-06-04",
                "status": "unknown",
            }
        )

    with pytest.raises(ValueError, match="requires future instrument_id"):
        parse_cash_discovery_report(
            {
                "schema_version": 1,
                "market_date": "2026-06-04",
                "status": "future_discovered",
                "future": {},
            }
        )


def test_planner_rejects_duplicate_dates_and_selected_overflow() -> None:
    with pytest.raises(ValueError, match="duplicate Cash discovery market date"):
        plan_cash_acquisition_cases(
            (
                discovered("2026-06-04"),
                discovered("2026-06-04"),
            ),
            template=template(),
        )

    with pytest.raises(ValueError, match="maximum is 1"):
        plan_cash_acquisition_cases(
            (
                discovered("2026-06-03"),
                discovered("2026-06-04"),
            ),
            template=template(),
            max_cases=1,
        )


def test_template_requires_explicit_consistent_utc_holding_period() -> None:
    with pytest.raises(ValueError, match="before expiry_at"):
        CashAcquisitionTemplate(
            future_id="BTC-USDT-260626",
            expiry_at="2026-06-26T08:00:00+00:00",
            exit_at="2026-06-27T00:00:00+00:00",
            entry_time_utc="00:15:00",
        )

    with pytest.raises(ValueError, match="differs from expiry_at"):
        CashAcquisitionTemplate(
            future_id="BTC-USDT-260925",
            expiry_at="2026-06-26T08:00:00+00:00",
            exit_at="2026-06-25T00:00:00+00:00",
            entry_time_utc="00:15:00",
        )

    with pytest.raises(ValueError, match="08:00:00 UTC"):
        CashAcquisitionTemplate(
            future_id="BTC-USDT-260626",
            expiry_at="2026-06-26T09:00:00+00:00",
            exit_at="2026-06-25T00:00:00+00:00",
            entry_time_utc="00:15:00",
        )

    with pytest.raises(ValueError, match="HH:MM:SS"):
        CashAcquisitionTemplate(
            future_id="BTC-USDT-260626",
            expiry_at="2026-06-26T08:00:00+00:00",
            exit_at="2026-06-25T00:00:00+00:00",
            entry_time_utc="00:15",
        )
