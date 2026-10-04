from datetime import UTC, datetime, timedelta
from decimal import Decimal

from future_opportunity.adapters.exchanges.okx.cash_and_carry import (
    OkxCashAndCarryMarketData,
)


def test_okx_cash_and_carry_filters_linear_live_future_contracts() -> None:
    now = datetime.now(UTC)
    future_ms = str(int((now + timedelta(days=30)).timestamp() * 1000))
    later_ms = str(int((now + timedelta(days=90)).timestamp() * 1000))
    expired_ms = str(int((now - timedelta(days=1)).timestamp() * 1000))

    instruments = [
        {
            "instId": "BTC-USDT-LATER",
            "state": "live",
            "ctType": "linear",
            "settleCcy": "USDT",
            "ctValCcy": "BTC",
            "ctVal": "0.01",
            "expTime": later_ms,
        },
        {
            "instId": "BTC-USDT-NEAR",
            "state": "live",
            "ctType": "linear",
            "settleCcy": "USDT",
            "ctValCcy": "BTC",
            "ctVal": "0.01",
            "expTime": future_ms,
        },
        {
            "instId": "BTC-USD-INVERSE",
            "state": "live",
            "ctType": "inverse",
            "settleCcy": "BTC",
            "ctValCcy": "USD",
            "ctVal": "100",
            "expTime": future_ms,
        },
        {
            "instId": "BTC-USDT-EXPIRED",
            "state": "live",
            "ctType": "linear",
            "settleCcy": "USDT",
            "ctValCcy": "BTC",
            "ctVal": "0.01",
            "expTime": expired_ms,
        },
    ]

    result = OkxCashAndCarryMarketData._eligible_futures(
        instruments,
        base="BTC",
        quote="USDT",
        now=now,
    )

    assert [item["instId"] for item in result] == [
        "BTC-USDT-NEAR",
        "BTC-USDT-LATER",
    ]


def test_okx_delivery_history_is_normalized_to_canonical_settlement() -> None:
    settled_at = datetime(2026, 12, 25, tzinfo=UTC)
    timestamp = str(int(settled_at.timestamp() * 1000))

    settlement = OkxCashAndCarryMarketData._find_delivery_settlement(
        {
            "code": "0",
            "data": [
                {
                    "ts": timestamp,
                    "details": [
                        {
                            "instId": "BTC-USDT-261225",
                            "px": "101234.5",
                            "type": "delivery",
                        }
                    ],
                }
            ],
        },
        canonical_instrument_id="okx:BTC-USDT-261225:future",
        raw_instrument_id="BTC-USDT-261225",
    )

    assert settlement is not None
    assert settlement.future_instrument_id == "okx:BTC-USDT-261225:future"
    assert settlement.settlement_price == Decimal("101234.5")
    assert settlement.settled_at == settled_at
