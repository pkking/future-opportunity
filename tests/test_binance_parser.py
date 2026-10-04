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
