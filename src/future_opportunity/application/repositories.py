from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from future_opportunity.domain.execution.model import Execution
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
)
from future_opportunity.domain.position.model import Position
from future_opportunity.domain.returns.model import ReturnAttribution
from future_opportunity.domain.risk.model import RiskReport
from future_opportunity.domain.strategy.model import StrategyPlan


class OpportunityRepository(Protocol):
    async def get_active_by_key(self, key: str) -> Opportunity | None:
        ...

    async def record(
        self,
        opportunity: Opportunity,
        observation: OpportunityObservation,
    ) -> None:
        """Persist aggregate state and its observation atomically."""
        ...


@dataclass(frozen=True, slots=True)
class SimulationRecord:
    plan: StrategyPlan
    execution: Execution
    position: Position
    entry_return: ReturnAttribution
    risk: RiskReport


class SimulationRepository(Protocol):
    async def record(self, simulation: SimulationRecord) -> None:
        """Persist the paper execution evidence atomically."""
        ...

    async def get(self, position_id: str) -> SimulationRecord | None:
        ...

    async def list(self) -> tuple[SimulationRecord, ...]:
        ...
