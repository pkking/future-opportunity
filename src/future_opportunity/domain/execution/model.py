from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class FillSource(StrEnum):
    SIMULATED = "simulated"
    EXCHANGE = "exchange"


@dataclass(frozen=True, slots=True)
class Fill:
    instrument_id: str
    side: str
    quantity: Decimal
    price: Decimal
    reference_price: Decimal
    notional: Decimal
    fee: Decimal
    slippage_bps: Decimal
    slippage_quote: Decimal
    filled_at: datetime
    source: FillSource
