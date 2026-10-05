from datetime import UTC, datetime

import pytest

from future_opportunity.adapters.historical.okx_mark_price import (
    OkxHistoricalMarkPriceQuery,
    parse_okx_mark_price_page,
)


def test_mark_price_page_normalizes_official_six_field_shape() -> None:
    candles = parse_okx_mark_price_page(
        {
            "code": "0",
            "msg": "",
            "data": [
                [
                    "1788220800000",
                    "108000",
                    "108100",
                    "107900",
                    "108050",
                    "1",
                ]
            ],
        },
        instrument_id="BTC-USDT-SWAP",
    )

    assert len(candles) == 1
    candle = candles[0]
    assert candle.started_at == datetime.fromtimestamp(1788220800, tz=UTC)
    assert candle.low_price < candle.close_price < candle.high_price
    assert candle.confirmed is True


def test_mark_price_parser_fails_closed_on_schema_drift() -> None:
    with pytest.raises(ValueError, match="must contain 6 fields"):
        parse_okx_mark_price_page(
            {
                "code": "0",
                "msg": "",
                "data": [["1", "2", "3", "4", "5"]],
            },
            instrument_id="BTC-USDT-SWAP",
        )


def test_mark_price_query_requires_one_minute_for_funding_bounds() -> None:
    with pytest.raises(ValueError, match="requires 1m"):
        OkxHistoricalMarkPriceQuery(
            instrument_id="BTC-USDT-SWAP",
            start_ms=1,
            end_ms=2,
            bar="5m",
        )
