from __future__ import annotations

import pytest

from future_opportunity.backtest.acquisition import (
    acquisition_dispatch_payload,
    acquisition_manifest_payload,
    parse_historical_acquisition_manifest,
    workflow_cash_cases_json,
    workflow_funding_dates_json,
)


def valid_manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "acquisition_id": "wave-01",
        "planner_campaign_prefix": "review-wave-01",
        "funding": {
            "start_date": "2026-09-04",
            "end_date": "2026-09-05",
        },
        "cash_cases": [
            {
                "entry_at": "2026-06-04T00:15:00+00:00",
                "exit_at": "2026-06-25T00:15:00+00:00",
                "future_id": "BTC-USDT-260626",
                "expiry_at": "2026-06-26T08:00:00+00:00",
            }
        ],
    }


def test_acquisition_manifest_resolves_funding_range_and_cash_cases() -> None:
    manifest = parse_historical_acquisition_manifest(valid_manifest())

    assert manifest.acquisition_id == "wave-01"
    assert manifest.funding is not None
    assert manifest.funding.source_kind == "range"
    assert manifest.funding.market_dates == (
        "2026-09-04",
        "2026-09-05",
    )
    assert len(manifest.cash_cases) == 1
    assert manifest.cash_cases[0].entry_market_date == "2026-06-04"
    assert manifest.total_items == 3
    assert workflow_funding_dates_json(manifest) == (
        '["2026-09-04","2026-09-05"]'
    )
    assert workflow_cash_cases_json(manifest) == (
        '[{"entry_at":"2026-06-04T00:15:00+00:00",'
        '"exit_at":"2026-06-25T00:15:00+00:00",'
        '"future_id":"BTC-USDT-260626",'
        '"expiry_at":"2026-06-26T08:00:00+00:00"}]'
    )

    payload = acquisition_manifest_payload(manifest)
    assert payload["total_items"] == 3
    assert payload["funding"]["market_dates"] == [
        "2026-09-04",
        "2026-09-05",
    ]


def test_acquisition_allows_funding_only_or_cash_only() -> None:
    funding_only = valid_manifest()
    funding_only["cash_cases"] = []
    assert parse_historical_acquisition_manifest(funding_only).total_items == 2

    cash_only = valid_manifest()
    cash_only["funding"] = None
    assert parse_historical_acquisition_manifest(cash_only).total_items == 1


def test_acquisition_requires_at_least_one_item() -> None:
    raw = valid_manifest()
    raw["funding"] = None
    raw["cash_cases"] = []

    with pytest.raises(ValueError, match="at least one Funding day or Cash case"):
        parse_historical_acquisition_manifest(raw)


def test_acquisition_rejects_large_ranges_and_total_size() -> None:
    raw = valid_manifest()
    raw["funding"] = {
        "start_date": "2026-09-01",
        "end_date": "2026-09-03",
    }

    with pytest.raises(ValueError, match="maximum is 2"):
        parse_historical_acquisition_manifest(
            raw,
            max_funding_days=2,
        )

    with pytest.raises(ValueError, match="maximum is 2"):
        parse_historical_acquisition_manifest(
            raw,
            max_total_items=2,
        )


def test_cash_cases_require_utc_order_future_identity_and_unique_market_date() -> None:
    wrong_order = valid_manifest()
    wrong_order["cash_cases"] = [
        {
            "entry_at": "2026-06-25T00:15:00+00:00",
            "exit_at": "2026-06-01T00:15:00+00:00",
            "future_id": "BTC-USDT-260626",
            "expiry_at": "2026-06-26T08:00:00+00:00",
        }
    ]
    with pytest.raises(ValueError, match="entry_at < exit_at < expiry_at"):
        parse_historical_acquisition_manifest(wrong_order)

    non_utc = valid_manifest()
    non_utc["cash_cases"][0]["entry_at"] = "2026-06-04T08:15:00+08:00"
    with pytest.raises(ValueError, match="must use UTC"):
        parse_historical_acquisition_manifest(non_utc)

    wrong_future = valid_manifest()
    wrong_future["cash_cases"][0]["future_id"] = "BTC-USDT-260925"
    with pytest.raises(ValueError, match="expiry date differs"):
        parse_historical_acquisition_manifest(wrong_future)

    wrong_expiry_time = valid_manifest()
    wrong_expiry_time["cash_cases"][0]["expiry_at"] = (
        "2026-06-26T09:00:00+00:00"
    )
    with pytest.raises(ValueError, match="08:00:00 UTC"):
        parse_historical_acquisition_manifest(wrong_expiry_time)

    duplicate_date = valid_manifest()
    duplicate_date["cash_cases"].append(
        {
            "entry_at": "2026-06-04T12:00:00+00:00",
            "exit_at": "2026-06-24T00:15:00+00:00",
            "future_id": "BTC-USDT-260626",
            "expiry_at": "2026-06-26T08:00:00+00:00",
        }
    )
    with pytest.raises(ValueError, match="duplicate Cash entry market date"):
        parse_historical_acquisition_manifest(duplicate_date)


def test_acquisition_rejects_schema_drift_and_unsafe_ids() -> None:
    raw = valid_manifest()
    raw["unexpected"] = True
    with pytest.raises(ValueError, match="fields differ from schema"):
        parse_historical_acquisition_manifest(raw)

    raw = valid_manifest()
    raw["acquisition_id"] = "../unsafe"
    with pytest.raises(ValueError, match="safe identifier"):
        parse_historical_acquisition_manifest(raw)


def test_acquisition_accepts_explicit_funding_dates_without_filling_gaps() -> None:
    raw = valid_manifest()
    raw["funding"] = {
        "market_dates": [
            "2026-01-01",
            "2026-01-08",
            "2026-01-13",
            "2026-01-22",
            "2026-01-29",
        ]
    }

    manifest = parse_historical_acquisition_manifest(raw)

    assert manifest.funding is not None
    assert manifest.funding.source_kind == "explicit_dates"
    assert manifest.funding.start_date is None
    assert manifest.funding.end_date is None
    assert manifest.funding.market_dates == (
        "2026-01-01",
        "2026-01-08",
        "2026-01-13",
        "2026-01-22",
        "2026-01-29",
    )
    assert acquisition_dispatch_payload(manifest)["funding"] == {
        "market_dates": [
            "2026-01-01",
            "2026-01-08",
            "2026-01-13",
            "2026-01-22",
            "2026-01-29",
        ]
    }
    assert workflow_funding_dates_json(manifest) == (
        '["2026-01-01","2026-01-08","2026-01-13","2026-01-22","2026-01-29"]'
    )


def test_explicit_funding_dates_reject_duplicates_order_drift_and_overflow() -> None:
    duplicate = valid_manifest()
    duplicate["funding"] = {
        "market_dates": ["2026-01-01", "2026-01-01"]
    }
    with pytest.raises(ValueError, match="duplicate Funding market date"):
        parse_historical_acquisition_manifest(duplicate)

    unordered = valid_manifest()
    unordered["funding"] = {
        "market_dates": ["2026-01-08", "2026-01-01"]
    }
    with pytest.raises(ValueError, match="strictly chronological"):
        parse_historical_acquisition_manifest(unordered)

    too_many = valid_manifest()
    too_many["funding"] = {
        "market_dates": ["2026-01-01", "2026-01-08", "2026-01-13"]
    }
    with pytest.raises(ValueError, match="maximum is 2"):
        parse_historical_acquisition_manifest(
            too_many,
            max_funding_days=2,
        )


def test_funding_shape_must_be_range_or_explicit_dates_but_not_both() -> None:
    raw = valid_manifest()
    raw["funding"] = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "market_dates": ["2026-01-08"],
    }

    with pytest.raises(ValueError, match="fields differ from schema"):
        parse_historical_acquisition_manifest(raw)
