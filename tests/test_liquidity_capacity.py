from datetime import UTC, datetime
from decimal import Decimal

from future_opportunity.domain.market.liquidity import max_visible_quantity_at_impact
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


def test_buy_capacity_solves_partial_level_at_vwap_threshold() -> None:
    now = datetime.now(UTC)
    book = OrderBook(
        bids=(OrderBookLevel(price=Decimal(99), quantity=Decimal(10)),),
        asks=(
            OrderBookLevel(price=Decimal(100), quantity=Decimal(10)),
            OrderBookLevel(price=Decimal(101), quantity=Decimal(10)),
        ),
        observed_at=now,
    )

    quantity = max_visible_quantity_at_impact(
        book,
        "buy",
        max_impact_bps=Decimal(50),
    )

    # Target VWAP is 100.5. Ten units at 100 plus ten at 101 reaches it exactly.
    assert quantity == Decimal(20)


def test_sell_capacity_stops_when_vwap_crosses_threshold() -> None:
    now = datetime.now(UTC)
    book = OrderBook(
        bids=(
            OrderBookLevel(price=Decimal(100), quantity=Decimal(10)),
            OrderBookLevel(price=Decimal(98), quantity=Decimal(10)),
        ),
        asks=(OrderBookLevel(price=Decimal(101), quantity=Decimal(10)),),
        observed_at=now,
    )

    quantity = max_visible_quantity_at_impact(
        book,
        "sell",
        max_impact_bps=Decimal(50),
    )

    # Target VWAP is 99.5: 10 @ 100 plus 10/3 @ 98.
    expected = Decimal(10) + Decimal(10) / Decimal(3)
    assert abs(quantity - expected) < Decimal("1e-20")
