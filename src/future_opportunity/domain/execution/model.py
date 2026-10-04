from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class FillSource(StrEnum):
    SIMULATED = "simulated"
    EXCHANGE = "exchange"


class ExecutionState(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionPurpose(StrEnum):
    OPEN = "open"
    CLOSE = "close"
    REBALANCE = "rebalance"


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


@dataclass(frozen=True, slots=True)
class Execution:
    id: str
    strategy_plan_id: str
    state: ExecutionState
    mode: str
    started_at: datetime
    finished_at: datetime | None
    fills: tuple[Fill, ...]
    purpose: ExecutionPurpose = ExecutionPurpose.OPEN
