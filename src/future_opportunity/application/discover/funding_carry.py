from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.ports import FundingCarryMarketDataPort
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

        opportunity_id = str(uuid4())
        observation_id = str(uuid4())
        key = (
            f"funding-carry:{snapshot.venue}:"
            f"{snapshot.spot_instrument_id}:{snapshot.perpetual_instrument_id}"
        )

        total_expected_cost = (
            evaluation.assumed_round_trip_fee_return
            + evaluation.estimated_round_trip_slippage_return
        )
        observation = OpportunityObservation(
            id=observation_id,
            opportunity_id=opportunity_id,
            observed_at=snapshot.observed_at,
            return_estimate=ReturnEstimate(
                character=ReturnCharacter.VARIABLE,
                expected_net_return=evaluation.expected_net_return_horizon,
                annualized_equivalent=evaluation.annualized_equivalent,
                expected_cost=total_expected_cost,
            ),
        )

        state = (
            OpportunityState.QUALIFIED
            if qualification.qualified
            else OpportunityState.DISCOVERED
        )
        opportunity = Opportunity(
            id=opportunity_id,
            key=key,
            strategy_type="funding-carry",
            state=state,
            discovered_at=snapshot.observed_at,
            qualified_at=snapshot.observed_at if qualification.qualified else None,
        )

        return DiscoveredFundingCarry(
            opportunity=opportunity,
            observation=observation,
            qualification=qualification,
            evaluation=evaluation,
        )
