from __future__ import annotations

import pytest

from future_opportunity.backtest.cash_source_readiness import (
    CASH_SOURCE_READINESS_DATES,
    CASH_SOURCE_READINESS_FAMILY,
    CASH_SOURCE_READINESS_MODULE,
    summarize_cash_source_readiness,
)


def _counts(value: int | None) -> dict[str, int | None]:
    return {
        market_date: value
        for market_date in CASH_SOURCE_READINESS_DATES
    }


def test_readiness_contract_reuses_exact_pre_registered_dates() -> None:
    assert len(CASH_SOURCE_READINESS_DATES) == 28
    assert len(set(CASH_SOURCE_READINESS_DATES)) == 28
    assert CASH_SOURCE_READINESS_DATES[0] == "2026-07-02"
    assert CASH_SOURCE_READINESS_DATES[-1] == "2026-09-20"
    assert CASH_SOURCE_READINESS_MODULE == "4"
    assert CASH_SOURCE_READINESS_FAMILY == "BTC-USDT"


def test_readiness_none_ready() -> None:
    result = summarize_cash_source_readiness(_counts(0))

    assert result["required_count"] == 28
    assert result["ready_count"] == 0
    assert result["missing_count"] == 28
    assert result["all_ready"] is False


def test_readiness_partial_and_error_states() -> None:
    counts = _counts(0)
    counts[CASH_SOURCE_READINESS_DATES[0]] = 1
    counts[CASH_SOURCE_READINESS_DATES[1]] = 2
    counts[CASH_SOURCE_READINESS_DATES[2]] = None

    result = summarize_cash_source_readiness(counts)

    assert result["ready_count"] == 1
    assert result["ambiguous_count"] == 1
    assert result["query_error_count"] == 1
    assert result["missing_count"] == 25
    assert result["all_ready"] is False


def test_readiness_all_ready() -> None:
    result = summarize_cash_source_readiness(_counts(1))

    assert result["ready_count"] == 28
    assert result["missing_count"] == 0
    assert result["ambiguous_count"] == 0
    assert result["query_error_count"] == 0
    assert result["all_ready"] is True


def test_readiness_rejects_incomplete_observations() -> None:
    counts = _counts(0)
    counts.pop(CASH_SOURCE_READINESS_DATES[-1])

    with pytest.raises(ValueError, match="exactly match canonical dates"):
        summarize_cash_source_readiness(counts)
