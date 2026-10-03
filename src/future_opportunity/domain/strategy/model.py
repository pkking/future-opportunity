from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class StrategyRef:
    name: str
    version: str


@dataclass(frozen=True, slots=True)
class PlanLeg:
    id: str
    instrument_id: str
    side: str
    target_notional: Money


@dataclass(frozen=True, slots=True)
class StrategyPlan:
    id: str
    strategy: StrategyRef
    opportunity_observation_id: str
    capital: Money
    legs: tuple[PlanLeg, ...]
    max_delta_pct: Decimal
    max_leverage: Decimal
    execution_mode: str = "paper"
