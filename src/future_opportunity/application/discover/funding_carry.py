from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.ports import FundingCarryMarketDataPort
from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
    OpportunityQualification,
    OpportunityState,
    ReturnCharacter,
    ReturnEstimate,
)
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    FundingCarryEvaluation,
    evaluate_funding_carry,
)


@dataclass(frozen=True, slots=True)
class DiscoveredFundingCarry:
    opportunity: Opportunity
    observation: OpportunityObservation
    qualification: OpportunityQualification
    evaluation: FundingCarryEvaluation


@dataclass(frozen=True, slots=True)
class DiscoverFundingCarry:
    market_data: FundingCarryMarketDataPort
    opportunities: OpportunityRepository

    async def execute(
        self,
        base: str,
        capital: Decimal,
        assumptions: FundingCarryAssumptions,
    ) -> DiscoveredFundingCarry:
        snapshot = await self.market_data.snapshot(base)
        evaluation = evaluate_funding_carry(snapshot, capital, assumptions)

        reasons: list[str] = []
        if evaluation.expected_funding_rate_per_period <= 0:
            reasons.append("expected_funding_not_positive")
        if evaluation.expected_net_return_horizon <= 0:
            reasons.append("expected_net_return_not_positive")

        qualification = OpportunityQualification(
            qualified=not reasons,
            reasons=tuple(reasons),
        )
        key = (
            f"funding-carry:{snapshot.venue}:"
            f"{snapshot.spot_instrument_id}:{snapshot.perpetual_instrument_id}"
        )

        opportunity = await self.opportunities.get_active_by_key(key)
        if opportunity is None:
            opportunity = Opportunity(
                id=str(uuid4()),
                key=key,
                strategy_type="funding-carry",
                state=(
                    OpportunityState.QUALIFIED
                    if qualification.qualified
                    else OpportunityState.DISCOVERED
                ),
                discovered_at=snapshot.observed_at,
                qualified_at=snapshot.observed_at if qualification.qualified else None,
            )
        elif qualification.qualified and opportunity.state is OpportunityState.DISCOVERED:
            opportunity.state = OpportunityState.QUALIFIED
            opportunity.qualified_at = snapshot.observed_at
        elif not qualification.qualified and opportunity.state is OpportunityState.QUALIFIED:
            opportunity.state = OpportunityState.EXPIRED
            opportunity.expired_at = snapshot.observed_at

        total_expected_cost = (
            evaluation.assumed_round_trip_fee_return
            + evaluation.estimated_round_trip_slippage_return
        )
        observation = OpportunityObservation(
            id=str(uuid4()),
            opportunity_id=opportunity.id,
            observed_at=snapshot.observed_at,
            return_estimate=ReturnEstimate(
                character=ReturnCharacter.VARIABLE,
                expected_net_return=evaluation.expected_net_return_horizon,
                annualized_equivalent=evaluation.annualized_equivalent,
                expected_cost=total_expected_cost,
            ),
        )

        await self.opportunities.save(opportunity)
        await self.opportunities.append_observation(observation)

        return DiscoveredFundingCarry(
            opportunity=opportunity,
            observation=observation,
            qualification=qualification,
            evaluation=evaluation,
        )
