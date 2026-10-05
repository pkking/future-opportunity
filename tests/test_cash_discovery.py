from datetime import UTC, datetime
from decimal import Decimal

import pytest

from future_opportunity.backtest.cash_discovery import (
    find_delivery_evidence,
    future_id_from_archive_member,
)


def test_future_id_is_discovered_from_verified_archive_member() -> None:
    assert future_id_from_archive_member(
        "BTC-USDT-260626-L2orderbook-400lv-2026-06-02.data",
        expected_market_date="2026-06-02",
    ) == "BTC-USDT-260626"


def test_future_member_rejects_date_or_shape_drift() -> None:
    with pytest.raises(ValueError, match="market date differs"):
        future_id_from_archive_member(
            "BTC-USDT-260626-L2orderbook-400lv-2026-06-02.data",
            expected_market_date="2026-06-03",
        )

    with pytest.raises(ValueError, match="unexpected BTC-USDT"):
        future_id_from_archive_member(
            "BTC-USDT-futureschain-L2orderbook-400lv-2026-06-02.data",
            expected_market_date="2026-06-02",
        )


def test_delivery_history_can_supply_explicit_historical_delivery_evidence() -> None:
    evidence = find_delivery_evidence(
        {
            "code": "0",
            "data": [
                {
                    "ts": "1782460800000",
                    "details": [
                        {
                            "instId": "BTC-USDT-260626",
                            "px": "61234.5",
                        }
                    ],
                }
            ],
        },
        future_id="BTC-USDT-260626",
    )

    assert evidence is not None
    assert evidence.instrument_id == "BTC-USDT-260626"
    assert evidence.delivered_at == datetime.fromtimestamp(
        1782460800,
        tz=UTC,
    )
    assert evidence.settlement_price == Decimal("61234.5")


def test_missing_delivery_history_remains_none() -> None:
    assert find_delivery_evidence(
        {"code": "0", "data": []},
        future_id="BTC-USDT-260626",
    ) is None
