from datetime import datetime
from decimal import Decimal

import pytest

from future_opportunity.adapters.historical.okx_catalog import (
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)


OFFICIAL_EXAMPLE = {
    "code": "0",
    "data": [
        {
            "dateAggrType": "daily",
            "details": [
                {
                    "dateRangeEnd": "1756656000000",
                    "dateRangeStart": "1756569600000",
                    "groupDetails": [
                        {
                            "dateTs": "1756656000000",
                            "filename": (
                                "BTC-USDT-SWAP-trades-2025-09-01.zip"
                            ),
                            "sizeMB": "10.82",
                            "url": (
                                "https://static.okx.com/cdn/okex/"
                                "traderecords/trades/daily/20250901/"
                                "BTC-USDT-SWAP-trades-2025-09-01.zip"
                            ),
                        }
                    ],
                    "groupSizeMB": "15.64",
                    "instFamily": "BTC-USDT",
                    "instId": "",
                    "instType": "SWAP",
                }
            ],
            "totalSizeMB": "15.64",
            "ts": "1756882260390",
        }
    ],
    "msg": "",
}


def test_okx_catalog_query_enforces_spot_vs_derivative_selectors() -> None:
    spot = OkxHistoricalCatalogQuery(
        module="4",
        instrument_type="SPOT",
        date_aggregation="daily",
        begin_ms=1,
        end_ms=2,
        instrument_ids=("BTC-USDT",),
    )
    swap = OkxHistoricalCatalogQuery(
        module="3",
        instrument_type="SWAP",
        date_aggregation="monthly",
        begin_ms=1,
        end_ms=2,
        instrument_families=("BTC-USDT",),
    )

    assert spot.params()["instIdList"] == "BTC-USDT"
    assert "instFamilyList" not in spot.params()
    assert swap.params()["instFamilyList"] == "BTC-USDT"
    assert "instIdList" not in swap.params()

    with pytest.raises(ValueError, match="SPOT history requires"):
        OkxHistoricalCatalogQuery(
            module="4",
            instrument_type="SPOT",
            date_aggregation="daily",
            begin_ms=1,
            end_ms=2,
        )


def test_okx_catalog_parser_normalizes_official_response_contract() -> None:
    query = OkxHistoricalCatalogQuery(
        module="1",
        instrument_type="SWAP",
        date_aggregation="daily",
        begin_ms=1756569600000,
        end_ms=1756656000000,
        instrument_families=("BTC-USDT",),
    )

    files = parse_okx_history_catalog(OFFICIAL_EXAMPLE, query)

    assert len(files) == 1
    item = files[0]
    assert item.instrument_type == "SWAP"
    assert item.instrument_family == "BTC-USDT"
    assert item.source_timezone == "UTC+08:00"
    assert item.filename == "BTC-USDT-SWAP-trades-2025-09-01.zip"
    assert item.declared_size_mb == Decimal("10.82")
    assert item.data_date == datetime.fromisoformat(
        "2025-09-01T00:00:00+08:00"
    )


def test_order_book_catalog_dates_use_utc() -> None:
    payload = {
        "code": "0",
        "msg": "",
        "data": [
            {
                "dateAggrType": "daily",
                "details": [
                    {
                        "instId": "BTC-USDT",
                        "instFamily": "",
                        "instType": "SPOT",
                        "dateRangeStart": "1756684800000",
                        "dateRangeEnd": "1756684800000",
                        "groupDetails": [
                            {
                                "dataTs": "1756684800000",
                                "filename": "book.zip",
                                "sizeMB": "1.25",
                                "url": "https://static.okx.com/book.zip",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    query = OkxHistoricalCatalogQuery(
        module="4",
        instrument_type="SPOT",
        date_aggregation="daily",
        begin_ms=1756684800000,
        end_ms=1756684800000,
        instrument_ids=("BTC-USDT",),
    )

    item = parse_okx_history_catalog(payload, query)[0]

    assert item.source_timezone == "UTC"
    assert item.data_date.isoformat() == "2025-09-01T00:00:00+00:00"
