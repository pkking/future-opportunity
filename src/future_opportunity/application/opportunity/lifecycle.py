from __future__ import annotations

from datetime import datetime

from future_opportunity.domain.opportunity.model import Opportunity, OpportunityState


def evolve_opportunity(
    current: Opportunity | None,
    *,
    opportunity_id: str,
    key: str,
    strategy_type: str,
    qualified: bool,
    observed_at: datetime,
) -> Opportunity:
    """Evolve one active Opportunity aggregate from qualification evidence."""

    if current is None:
        return Opportunity(
            id=opportunity_id,
            key=key,
            strategy_type=strategy_type,
            state=(
                OpportunityState.QUALIFIED
                if qualified
                else OpportunityState.DISCOVERED
            ),
            discovered_at=observed_at,
            qualified_at=observed_at if qualified else None,
        )

    if qualified and current.state is OpportunityState.DISCOVERED:
        current.state = OpportunityState.QUALIFIED
        current.qualified_at = observed_at
    elif not qualified and current.state is OpportunityState.QUALIFIED:
        current.state = OpportunityState.EXPIRED
        current.expired_at = observed_at

    return current
