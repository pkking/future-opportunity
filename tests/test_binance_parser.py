from datetime import UTC, datetime
from decimal import Decimal

from future_opportunity.adapters.exchanges.binance.market_data import BinanceFundingMarketData


def test_binance_order_book_is_normalized() -> None:
    now = datetime.now(UTC)
    book = BinanceFundingMarketData._parse_book(
        {
            "bids": [["100.0", "2.0"], ["99.0", "3.0"]],
            "asks": [["101.0", "4.0"], ["102.0", "5.0"]],
        },
        now,
    )

    assert book.best_bid == Decimal(100)
    assert book.best_ask == Decimal(101)
    assert book.bids[0].quantity == Decimal(2)


def test_binance_funding_history_preserves_mark_price_and_rate_type() -> None:
    history = BinanceFundingMarketData._parse_funding_history(
        [
            {
                "fundingRate": "0.0001",
                "fundingTime": "1760000000000",
                "markPrice": "120000.5",
                "rateType": "Regular",
            }
        ]
    )

    assert history[0].rate == Decimal("0.0001")
    assert history[0].mark_price == Decimal("120000.5")
    assert history[0].rate_type == "Regular"
