from datetime import UTC, datetime
from decimal import Decimal

import pytest

from future_opportunity.backtest.compact import compact_order_book_observation
from future_opportunity.backtest.model import HistoricalOrderBookObservation
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def observation() -> HistoricalOrderBookObservation:
    return HistoricalOrderBookObservation(
        instrument_id="BTC-USDT",
        action="update",
        source_line=42,
        observed_at=NOW,
        book=OrderBook(
            bids=(
                OrderBookLevel(price=Decimal("100"), quantity=Decimal("0.3")),
                OrderBookLevel(price=Decimal("99"), quantity=Decimal("0.5")),
                OrderBookLevel(price=Decimal("98"), quantity=Decimal("1")),
            ),
            asks=(
                OrderBookLevel(price=Decimal("101"), quantity=Decimal("0.2")),
                OrderBookLevel(price=Decimal("102"), quantity=Decimal("0.7")),
                OrderBookLevel(price=Decimal("103"), quantity=Decimal("1")),
            ),
            observed_at=NOW,
        ),
    )


def test_compact_book_retains_minimum_best_price_outward_depth() -> None:
    compact, evidence = compact_order_book_observation(
        observation(),
        preserve_base_quantity=Decimal("0.6"),
    )

    assert [level.price for level in compact.book.bids] == [
        Decimal("100"),
        Decimal("99"),
    ]
    assert [level.price for level in compact.book.asks] == [
        Decimal("101"),
        Decimal("102"),
    ]
    assert evidence.retained_bid_quantity == Decimal("0.8")
    assert evidence.retained_ask_quantity == Decimal("0.9")
    assert evidence.compact_bid_levels == 2
    assert evidence.compact_ask_levels == 2
    assert compact.source_line == 42


def test_compact_book_rejects_insufficient_depth() -> None:
    with pytest.raises(ValueError, match="bids depth"):
        compact_order_book_observation(
            observation(),
            preserve_base_quantity=Decimal("2"),
        )
