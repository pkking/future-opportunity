from __future__ import annotations

import pytest

from future_opportunity.backtest.cash_expiry_probe import (
    CASH_EXPIRY_PROBE_TARGETS,
    CashExpiryProbeResult,
    cash_expiry_probe_summary,
    evaluate_cash_expiry_probe,
)


def report(date: str, future: str) -> dict[str, object]:
    return {
        "market_date": date,
        "status": "multiple_future_contracts",
        "catalog": {
            "raw_sha256": "a" * 64,
            "archive_members": [
                f"{future}-L2orderbook-400lv-{date}.data",
                f"BTC-USDT-260327-L2orderbook-400lv-{date}.data",
            ],
        },
        "future_candidates": [
            {"instrument_id": future},
            {"instrument_id": "BTC-USDT-260327"},
        ],
    }


def test_exact_historical_quarterly_future_identity() -> None:
    day, future = CASH_EXPIRY_PROBE_TARGETS[0]
    result = evaluate_cash_expiry_probe(
        report(day, future),
        market_date=day,
        expected_future_id=future,
    )
    assert result.status == "identity_verified"
    assert result.raw_archive_sha256 == "a" * 64
    assert "not_exit_or_pnl_evidence" in result.reason


def test_missing_archive_is_explicitly_unavailable() -> None:
    day, future = CASH_EXPIRY_PROBE_TARGETS[0]
    result = evaluate_cash_expiry_probe(
        {"market_date": day, "status": "no_unique_future_chain_archive"},
        market_date=day,
        expected_future_id=future,
    )
    assert result.status == "unavailable"
    assert result.raw_archive_sha256 is None


def test_wrong_quarterly_future_does_not_pass() -> None:
    day, future = CASH_EXPIRY_PROBE_TARGETS[0]
    result = evaluate_cash_expiry_probe(
        report(day, "BTC-USDT-260327"),
        market_date=day,
        expected_future_id=future,
    )
    assert result.status == "unavailable"


def test_wrong_market_date_and_duplicate_archive_member_fail_closed() -> None:
    day, future = CASH_EXPIRY_PROBE_TARGETS[0]
    with pytest.raises(ValueError, match="date differs"):
        evaluate_cash_expiry_probe(
            report(day, future), market_date="2025-09-13",
            expected_future_id=future,
        )
    value = report(day, future)
    value["catalog"]["archive_members"].append(
        f"folder/{future}-L2orderbook-400lv-{day}.data"
    )
    result = evaluate_cash_expiry_probe(
        value, market_date=day, expected_future_id=future,
    )
    assert result.status == "unavailable"


def test_probe_summary_never_claims_acquisition_readiness() -> None:
    results = [
        CashExpiryProbeResult(day, future, "identity_verified", "archive", "a" * 64)
        for day, future in CASH_EXPIRY_PROBE_TARGETS
    ]
    summary = cash_expiry_probe_summary(results)
    assert summary["probe_target_count"] == 4
    assert summary["archive_identity_verified_count"] == 4
    assert summary["target_coverage_complete"] is True
    assert summary["acquisition_ready"] is False
    with pytest.raises(ValueError, match="duplicate"):
        cash_expiry_probe_summary(results + results[:1])
