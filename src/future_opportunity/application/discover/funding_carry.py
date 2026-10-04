from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.ports import FundingCarryMarketDataPort
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
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
    evaluation: FundingCarryEvaluation


@dataclass(frozen=True, slots=True)
class DiscoverFundingCarry:
    market_data: FundingCarryMarketDataPort

    async def execute(
        self,
        base: str,
        capital: Decimal,
        assumptions: FundingCarryAssumptions,
    ) -> DiscoveredFundingCarry:
        snapshot = await self.market_data.snapshot(base)
        evaluation = evaluate_funding_carry(snapshot, capital, assumptions)

        opportunity_id = str(uuid4())
        observation_id = str(uuid4())
        key = (
            f"funding-carry:{snapshot.venue}:"
            f"{snapshot.spot_instrument_id}:{snapshot.perpetual_instrument_id}"
        )

        observation = OpportunityObservation(
            id=observation_id,
            opportunity_id=opportunity_id,
            observed_at=snapshot.observed_at,
            return_estimate=ReturnEstimate(
                character=ReturnCharacter.VARIABLE,
                expected_net_return=evaluation.expected_net_return_horizon,
                annualized_equivalent=evaluation.annualized_equivalent,
                expected_cost=evaluation.assumed_round_trip_fee_return,
            ),
        )
        opportunity = Opportunity(
            id=opportunity_id,
            key=key,
            strategy_type="funding-carry",
            state=OpportunityState.QUALIFIED,
            discovered_at=snapshot.observed_at,
            qualified_at=snapshot.observed_at,
        )

        return DiscoveredFundingCarry(
            opportunity=opportunity,
            observation=observation,
            evaluation=evaluation,
        )
