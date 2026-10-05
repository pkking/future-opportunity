import pytest

from future_opportunity.backtest.date_range import (
    historical_date_range,
    historical_date_range_json,
)


def test_historical_date_range_is_inclusive_and_ordered() -> None:
    assert historical_date_range("2026-09-01", "2026-09-03") == (
        "2026-09-01",
        "2026-09-02",
        "2026-09-03",
    )
    assert historical_date_range_json(
        "2026-09-01",
        "2026-09-03",
    ) == '["2026-09-01","2026-09-02","2026-09-03"]'


def test_historical_date_range_rejects_invalid_order_and_large_batch() -> None:
    with pytest.raises(ValueError, match="before start_date"):
        historical_date_range("2026-09-03", "2026-09-01")

    with pytest.raises(ValueError, match="maximum is 2"):
        historical_date_range(
            "2026-09-01",
            "2026-09-03",
            max_days=2,
        )


def test_historical_date_range_rejects_non_iso_date() -> None:
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        historical_date_range("2026/09/01", "2026-09-03")
