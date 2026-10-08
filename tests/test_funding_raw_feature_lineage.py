from __future__ import annotations

import copy
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from future_opportunity.backtest.funding_raw_feature_lineage import (
    reconstruct_funding_regime_features,
)
from future_opportunity.backtest.funding_regime_research import (
    plan_funding_regime_research,
)


def _ms(moment: datetime) -> str:
    return str(int(moment.timestamp() * 1000))


def make_capture() -> dict:
    start = date(2026, 9, 15)
    # Ten distinct complete UTC candles for three candidate entry dates.
    candles = []
    for i in range(10):
        opened = datetime(2026, 9, 7, tzinfo=UTC) + timedelta(days=i)
        close = str(Decimal(100) + Decimal(i * i + 1))
        candles.append(
            [_ms(opened), close, close, close, close, "1", "1", "1", "1"]
        )
    funding = []
    for i in range(3):
        market = start + timedelta(days=i)
        event = datetime.combine(
            market - timedelta(days=1),
            datetime.min.time(),
            tzinfo=UTC,
        ) + timedelta(hours=16)
        funding.append(
            {
                "fundingTime": _ms(event),
                "instId": "BTC-USDT-SWAP",
                "instType": "SWAP",
                "fundingRate": "0.004",  # Predicted value must not be used.
                "realizedRate": "-0.00015" if i == 0 else "0.00005",
            }
        )
    return {
        "schema_version": 1,
        "captured_at": "2026-10-09T00:00:00+00:00",
        "start_date": "2026-09-15",
        "end_date": "2026-09-17",
        "seed": "fixed-before-inspection",
        "requested_per_regime": 1,
        "pinned_market_dates": [],
        "funding_query": {"instId": "BTC-USDT-SWAP", "limit": "400"},
        "funding_response": {"code": "0", "data": funding, "msg": ""},
        "spot_query": {
            "instId": "BTC-USDT", "bar": "1Dutc", "limit": "100"
        },
        "spot_response": {"code": "0", "data": candles, "msg": ""},
    }


def test_reconstructs_reproducible_event_time_only_features() -> None:
    raw = make_capture()
    result = reconstruct_funding_regime_features(raw)

    assert result == reconstruct_funding_regime_features(copy.deepcopy(raw))
    assert result["feature_rows_reconstructed"] == 3
    assert result["missing_days"] == []
    assert result["source_authentication_status"] == "requires_independent_review"
    assert result["point_in_time_publication_verified"] is False
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False
    rows = result["planner_input"]["observations"]
    assert len(rows) == 3
    assert rows[0]["lagged_funding_rate"] == "-0.00015"
    assert rows[0]["lagged_funding_rate"] != raw["funding_response"]["data"][0][
        "fundingRate"
    ]
    assert rows[0]["funding_observed_at"] == "2026-09-14T16:00:00+00:00"
    assert rows[0]["features_observed_at"] == "2026-09-15T00:00:00+00:00"
    assert rows[0]["volatility_window_end_at"] == "2026-09-15T00:00:00+00:00"
    assert Decimal(rows[0]["trailing_spot_volatility_bps"]) >= 0
    assert rows[0]["source_record_sha256"] != rows[1]["source_record_sha256"]
    selection = plan_funding_regime_research(result["planner_input"])
    assert selection["acquisition_approved"] is False
    assert selection["market_wide_opportunity_arrival_rate"] is None
    assert selection["selection_uses_qualified_or_return_outcomes"] is False


def test_missing_spot_candle_remains_explicit_missing() -> None:
    raw = make_capture()
    raw["spot_response"]["data"] = [
        item for item in raw["spot_response"]["data"]
        if item[0] != _ms(datetime(2026, 9, 14, tzinfo=UTC))
    ]
    result = reconstruct_funding_regime_features(raw)
    assert "2026-09-15" in result["planner_input"]["missing_market_dates"]
    assert "missing_or_unconfirmed_8_daily_spot_candles" in (
        result["missing_days"][0]["reasons"]
    )
    assert len(result["planner_input"]["observations"]) == 1


def test_unconfirmed_spot_candle_is_not_used() -> None:
    raw = make_capture()
    raw["spot_response"]["data"][7][8] = "0"
    result = reconstruct_funding_regime_features(raw)
    assert "2026-09-15" in result["planner_input"]["missing_market_dates"]


def test_stale_funding_remains_missing_without_forward_leakage() -> None:
    raw = make_capture()
    raw["funding_response"]["data"] = raw["funding_response"]["data"][:1]
    result = reconstruct_funding_regime_features(raw)
    assert "2026-09-17" in result["planner_input"]["missing_market_dates"]
    assert "missing_or_stale_prior_settled_funding" in (
        result["missing_days"][-1]["reasons"]
    )


def test_funding_one_hour_guard_never_uses_just_settled_event() -> None:
    raw = make_capture()
    raw["funding_response"]["data"][0]["fundingTime"] = _ms(
        datetime(2026, 9, 15, tzinfo=UTC)
    )
    result = reconstruct_funding_regime_features(raw)
    # 00:00 funding would be only 15 minutes old at 00:15 entry.
    assert "2026-09-15" in result["planner_input"]["missing_market_dates"]


def test_raw_response_modification_changes_digest_and_features() -> None:
    raw = make_capture()
    base = reconstruct_funding_regime_features(raw)
    raw["spot_response"]["data"][0][4] = "110"
    changed = reconstruct_funding_regime_features(raw)
    assert changed["source_sha256"] != base["source_sha256"]
    assert changed["planner_input"]["observations"][0][
        "source_record_sha256"
    ] != base["planner_input"]["observations"][0]["source_record_sha256"]


@pytest.mark.parametrize("change", ["funding", "spot"])
def test_duplicate_source_record_fails_closed(change: str) -> None:
    raw = make_capture()
    key = "funding_response" if change == "funding" else "spot_response"
    raw[key]["data"].append(copy.deepcopy(raw[key]["data"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        reconstruct_funding_regime_features(raw)


def test_rejects_invalid_source_instrument_and_non_finite_price() -> None:
    raw = make_capture()
    raw["funding_response"]["data"][0]["instId"] = "ETH-USDT-SWAP"
    with pytest.raises(ValueError, match="instrument"):
        reconstruct_funding_regime_features(raw)
    raw = make_capture()
    raw["spot_response"]["data"][0][4] = "NaN"
    with pytest.raises(ValueError, match="finite"):
        reconstruct_funding_regime_features(raw)


def test_rejects_surplus_outcome_fields_and_unexpected_queries() -> None:
    raw = make_capture()
    raw["expected_net_return"] = "0.2"
    with pytest.raises(ValueError, match="schema"):
        reconstruct_funding_regime_features(raw)
    raw = make_capture()
    raw["spot_query"]["bar"] = "1D"
    with pytest.raises(ValueError, match="SPOT"):
        reconstruct_funding_regime_features(raw)
