from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from future_opportunity.domain.execution.model import Fill, FillSource
from future_opportunity.domain.market.liquidity import estimate_market_fill
from future_opportunity.domain.market.snapshot import OrderBook


BPS = Decimal(10_000)


@dataclass(frozen=True, slots=True)
class PaperExecutionResult:
    fill: Fill


def simulate_market_fill(
    instrument_id: str,
    side: str,
    quantity: Decimal,
    book: OrderBook,
    fee_bps: Decimal,
) -> PaperExecutionResult:
    estimate = estimate_market_fill(book, side, quantity)
    reference = book.best_ask if side == "buy" else book.best_bid
    reference_notional = quantity * reference
    slippage_quote = (
        estimate.notional - reference_notional
        if side == "buy"
        else reference_notional - estimate.notional
    )

    return PaperExecutionResult(
        fill=Fill(
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
            price=estimate.price,
            reference_price=reference,
            notional=estimate.notional,
            fee=estimate.notional * fee_bps / BPS,
            slippage_bps=estimate.impact_bps,
            slippage_quote=slippage_quote,
            filled_at=datetime.now(UTC),
            source=FillSource.SIMULATED,
        )
    )
