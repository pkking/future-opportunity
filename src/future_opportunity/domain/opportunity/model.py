from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class OpportunityState(StrEnum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    EXPIRED = "expired"


class ReturnCharacter(StrEnum):
    VARIABLE = "variable"
    CONVERGENT = "convergent"


@dataclass(frozen=True, slots=True)
class ReturnEstimate:
    character: ReturnCharacter
    expected_net_return: Decimal
    annualized_equivalent: Decimal
    expected_cost: Decimal


@dataclass(frozen=True, slots=True)
class OpportunityObservation:
    id: str
    opportunity_id: str
    observed_at: datetime
    return_estimate: ReturnEstimate
    capacity_5bps: Decimal | None = None
    capacity_10bps: Decimal | None = None


@dataclass(slots=True)
class Opportunity:
    id: str
    key: str
    strategy_type: str
    state: OpportunityState
    discovered_at: datetime
    qualified_at: datetime | None = None
    expired_at: datetime | None = None
