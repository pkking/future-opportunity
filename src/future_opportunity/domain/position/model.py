from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class PositionState(StrEnum):
    PLANNED = "planned"
    OPENING = "opening"
    HEDGED = "hedged"
    ACTIVE = "active"
    REBALANCING = "rebalancing"
    DEGRADED = "degraded"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class LegPosition:
    instrument_id: str
    quantity: Decimal
    notional: Decimal


@dataclass(slots=True)
class Position:
    id: str
    strategy_plan_id: str
    state: PositionState
    legs: tuple[LegPosition, ...]
    delta_notional: Decimal
    delta_pct: Decimal
    realized_pnl: Decimal = Decimal(0)
    unrealized_pnl: Decimal = Decimal(0)
    version: int = 0
