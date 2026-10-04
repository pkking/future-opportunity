from __future__ import annotations

from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
)


class MemoryOpportunityRepository(OpportunityRepository):
    def __init__(self) -> None:
        self._opportunities: dict[str, Opportunity] = {}
        self._observations: dict[str, list[OpportunityObservation]] = {}

    async def get_active_by_key(self, key: str) -> Opportunity | None:
        opportunity = self._opportunities.get(key)
        if opportunity is None or opportunity.expired_at is not None:
            return None
        return opportunity

    async def record(
        self,
        opportunity: Opportunity,
        observation: OpportunityObservation,
    ) -> None:
        self._opportunities[opportunity.key] = opportunity
        self._observations.setdefault(observation.opportunity_id, []).append(observation)

    def observations_for(self, opportunity_id: str) -> tuple[OpportunityObservation, ...]:
        return tuple(self._observations.get(opportunity_id, ()))
