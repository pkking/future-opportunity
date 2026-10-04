from datetime import UTC, datetime
from uuid import uuid4

from future_opportunity.application.opportunity.lifecycle import evolve_opportunity
from future_opportunity.domain.opportunity.model import OpportunityState


def test_opportunity_promotes_then_expires() -> None:
    now = datetime.now(UTC)
    opportunity = evolve_opportunity(
        None,
        opportunity_id=str(uuid4()),
        key="funding-carry:venue:spot:perp",
        strategy_type="funding-carry",
        qualified=False,
        observed_at=now,
    )
    assert opportunity.state is OpportunityState.DISCOVERED

    opportunity = evolve_opportunity(
        opportunity,
        opportunity_id="ignored-for-existing-aggregate",
        key=opportunity.key,
        strategy_type=opportunity.strategy_type,
        qualified=True,
        observed_at=now,
    )
    assert opportunity.state is OpportunityState.QUALIFIED
    assert opportunity.qualified_at == now

    opportunity = evolve_opportunity(
        opportunity,
        opportunity_id="ignored-for-existing-aggregate",
        key=opportunity.key,
        strategy_type=opportunity.strategy_type,
        qualified=False,
        observed_at=now,
    )
    assert opportunity.state is OpportunityState.EXPIRED
    assert opportunity.expired_at == now
