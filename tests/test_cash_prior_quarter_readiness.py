from __future__ import annotations

from datetime import date, timedelta

import pytest

from future_opportunity.backtest.cash_prior_quarter_readiness import (
    QUARTERS,
    SPOT_CATALOG_DATES,
    paired_source_readiness,
    quarter_capacity_report,
)


def all_2025_archive_counts() -> dict[str, int | None]:
    start, end = date(2025, 7, 1), date(2025, 12, 25)
    return {
        (start + timedelta(days=i)).isoformat(): 1
        for i in range((end - start).days + 1)
    }


def good_spot() -> dict[str, dict[str, str | None]]:
    return {
        day: {
            "status": "unique_catalog_source",
            "reason": "catalog_metadata_only_not_orderbook_sample",
            "filename": f"BTC-USDT-SPOT-{day}.tar.gz",
        }
        for day in SPOT_CATALOG_DATES
    }


def good_exit() -> dict[str, dict[str, str | None]]:
    return {
        spec["exit_market_date"]: {
            "status": "identity_verified",
            "reason": "archive_member_only_not_exit_or_pnl_evidence",
            "raw_sha256": "a" * 64,
        }
        for spec in QUARTERS.values()
    }


def test_quarter_capacity_preserves_expiry_boundaries() -> None:
    result = quarter_capacity_report(all_2025_archive_counts())
    assert result["2025-Q3"]["scanned_date_count"] == 87
    assert result["2025-Q4"]["scanned_date_count"] == 90
    for item in result.values():
        assert item["source_calendar_complete"] is True
        assert item["exact_future_identity_for_each_day_verified"] is False


def test_missing_ambiguous_and_error_dates_are_not_ready() -> None:
    raw = all_2025_archive_counts()
    raw["2025-08-01"] = 0
    raw["2025-10-01"] = 2
    raw["2025-11-01"] = None
    result = quarter_capacity_report(raw)
    assert result["2025-Q3"]["missing_days"] == ["2025-08-01"]
    assert result["2025-Q4"]["ambiguous_days"] == ["2025-10-01"]
    assert result["2025-Q4"]["query_error_days"] == ["2025-11-01"]
    assert result["2025-Q3"]["source_calendar_complete"] is False
    assert result["2025-Q4"]["source_calendar_complete"] is False


def test_missing_calendar_day_fails_closed() -> None:
    raw = all_2025_archive_counts()
    raw.pop("2025-07-02")
    with pytest.raises(ValueError, match="every quarter day"):
        quarter_capacity_report(raw)


def test_full_catalog_and_exit_identity_still_not_acquisition_ready() -> None:
    result = paired_source_readiness(
        all_2025_archive_counts(),
        spot_catalog=good_spot(),
        futures_exit=good_exit(),
    )
    assert result["spot_fixed_dates_catalog_ready"] is True
    assert result["future_exit_archive_identity_ready"] is True
    assert result["entry_exit_orderbook_snapshots_verified"] is False
    assert result["acquisition_ready"] is False
    assert result["no_economics_inspected"] is True


def test_spot_missing_source_or_invalid_exit_digest_cannot_pass() -> None:
    spot = good_spot()
    spot["2025-09-12"]["status"] = "unavailable"
    res = paired_source_readiness(
        all_2025_archive_counts(), spot_catalog=spot, futures_exit=good_exit(),
    )
    assert res["spot_fixed_dates_catalog_ready"] is False
    exit_sources = good_exit()
    exit_sources["2025-12-25"]["raw_sha256"] = None
    res = paired_source_readiness(
        all_2025_archive_counts(),
        spot_catalog=good_spot(),
        futures_exit=exit_sources,
    )
    assert res["future_exit_archive_identity_ready"] is False


def test_missing_fixed_exit_or_spot_target_fails() -> None:
    spots = good_spot()
    spots.pop("2025-09-12")
    with pytest.raises(ValueError, match="all six fixed dates"):
        paired_source_readiness(
            all_2025_archive_counts(),
            spot_catalog=spots,
            futures_exit=good_exit(),
        )
    exits = good_exit()
    exits.pop("2025-12-25")
    with pytest.raises(ValueError, match="both fixed dates"):
        paired_source_readiness(
            all_2025_archive_counts(),
            spot_catalog=good_spot(),
            futures_exit=exits,
        )
