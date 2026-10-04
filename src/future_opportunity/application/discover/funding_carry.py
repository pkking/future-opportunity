from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.opportunity.lifecycle import evolve_opportunity
from future_opportunity.domain.deployment.model import (
    DeploymentAssessment,
    LiquidityPolicy,
    assess_liquidity_bounded_deployment,
)
from future_opportunity.domain.market.liquidity import hedged_visible_spot_notional_capacity
from future_opportunity.application.ports import FundingCarryMarketDataPort
from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.domain.market.snapshot import FundingCarryMarketSnapshot
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
    OpportunityQualification,
    ReturnCharacter,
    ReturnEstimate,
)
from future_opportunity.domain.strategy.definition import FUNDING_CARRY
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    FundingCarryEvaluation,
    evaluate_funding_carry,
)


@dataclass(frozen=True, slots=True)
class DiscoveredFundingCarry:
    snapshot: FundingCarryMarketSnapshot
    opportunity: Opportunity
    observation: OpportunityObservation
    qualification: OpportunityQualification
    evaluation: FundingCarryEvaluation
    deployment: DeploymentAssessment


@dataclass(frozen=True, slots=True)
class DiscoverFundingCarry:
    market_data: FundingCarryMarketDataPort
    opportunities: OpportunityRepository

    async def execute(
        self,
        base: str,
        capital: Decimal,
        assumptions: FundingCarryAssumptions,
        liquidity_policy: LiquidityPolicy = LiquidityPolicy.STRICT,
        max_impact_bps: Decimal = Decimal(10),
    ) -> DiscoveredFundingCarry:
        snapshot = await self.market_data.snapshot(base)
        capacity = hedged_visible_spot_notional_capacity(
            snapshot.spot_book,
            snapshot.perpetual_book,
            max_impact_bps,
        )
        deployment = assess_liquidity_bounded_deployment(
            capital=capital,
            reserve_ratio=assumptions.reserve_ratio,
            futures_leverage=assumptions.futures_leverage,
            hedge_notional_ratio=Decimal(1),
            capacity_spot_notional=capacity,
            policy=liquidity_policy,
            max_impact_bps=max_impact_bps,
        )
        evaluation = evaluate_funding_carry(
            snapshot,
            capital,
            assumptions,
            deployed_spot_notional=deployment.assessed_spot_notional,
        )

        reasons: list[str] = []
        if (
            deployment.policy is LiquidityPolicy.STRICT
            and not deployment.capacity_sufficient
        ):
            reasons.append("requested_notional_exceeds_liquidity_limit")
        elif not deployment.executable:
            reasons.append("no_executable_liquidity")

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

        opportunity = evolve_opportunity(
            await self.opportunities.get_active_by_key(key),
            opportunity_id=str(uuid4()),
            key=key,
            strategy_type=FUNDING_CARRY.name,
            qualified=qualification.qualified,
            observed_at=snapshot.observed_at,
        )

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
            capacity_5bps=evaluation.visible_capacity_5bps,
            capacity_10bps=evaluation.visible_capacity_10bps,
        )

        await self.opportunities.record(opportunity, observation)

        return DiscoveredFundingCarry(
            snapshot=snapshot,
            opportunity=opportunity,
            observation=observation,
            qualification=qualification,
            evaluation=evaluation,
            deployment=deployment,
        )
