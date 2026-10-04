from datetime import UTC, datetime, timedelta

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
            "settleCcy": "USDT",
            "ctValCcy": "BTC",
            "ctVal": "0.01",
            "expTime": later_ms,
        },
        {
            "instId": "BTC-USDT-NEAR",
            "state": "live",
            "settleCcy": "USDT",
            "ctValCcy": "BTC",
            "ctVal": "0.01",
            "expTime": future_ms,
        },
        {
            "instId": "BTC-USD-INVERSE",
            "state": "live",
            "settleCcy": "BTC",
            "ctValCcy": "USD",
            "ctVal": "100",
            "expTime": future_ms,
        },
        {
            "instId": "BTC-USDT-EXPIRED",
            "state": "live",
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
