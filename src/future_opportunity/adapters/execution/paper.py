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

    return PaperExecutionResult(
        fill=Fill(
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
            price=estimate.price,
            notional=estimate.notional,
            fee=estimate.notional * fee_bps / BPS,
            slippage_bps=estimate.impact_bps,
            filled_at=datetime.now(UTC),
            source=FillSource.SIMULATED,
        )
    )
