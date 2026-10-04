from __future__ import annotations

from typing import Protocol

from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
)


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
