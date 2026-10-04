from datetime import UTC, datetime
from decimal import Decimal

from future_opportunity.adapters.exchanges.okx.common import parse_okx_book


def test_okx_swap_contract_sizes_are_normalized_to_base_quantity() -> None:
    now = datetime.now(UTC)
    book = parse_okx_book(
        {
            "bids": [["100000", "12", "0", "2"]],
            "asks": [["100010", "7", "0", "1"]],
        },
        now,
        quantity_multiplier=Decimal("0.01"),
    )

    assert book.best_bid == Decimal(100_000)
    assert book.bids[0].quantity == Decimal("0.12")
    assert book.asks[0].quantity == Decimal("0.07")
