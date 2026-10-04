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
from future_opportunity.application.ports import CashAndCarryMarketDataPort
from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
    OpportunityQualification,
    ReturnCharacter,
    ReturnEstimate,
)
from future_opportunity.domain.strategy.definition import CASH_AND_CARRY
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
    CashAndCarryEvaluation,
    evaluate_cash_and_carry,
)


@dataclass(frozen=True, slots=True)
class DiscoveredCashAndCarry:
    snapshot: CashAndCarryMarketSnapshot
    opportunity: Opportunity
    observation: OpportunityObservation
    qualification: OpportunityQualification
    evaluation: CashAndCarryEvaluation
    deployment: DeploymentAssessment


@dataclass(frozen=True, slots=True)
class DiscoverCashAndCarry:
    market_data: CashAndCarryMarketDataPort
    opportunities: OpportunityRepository

    async def execute(
        self,
        base: str,
        capital: Decimal,
        assumptions: CashAndCarryAssumptions,
        liquidity_policy: LiquidityPolicy = LiquidityPolicy.STRICT,
        max_impact_bps: Decimal = Decimal(10),
    ) -> tuple[DiscoveredCashAndCarry, ...]:
        snapshots = await self.market_data.snapshots(base)
        results: list[DiscoveredCashAndCarry] = []

        for snapshot in snapshots:
            hedge_ratio = (
                snapshot.future_book.best_bid / snapshot.spot_book.best_ask
            )
            capacity = hedged_visible_spot_notional_capacity(
                snapshot.spot_book,
                snapshot.future_book,
                max_impact_bps,
            )
            deployment = assess_liquidity_bounded_deployment(
                capital=capital,
                reserve_ratio=assumptions.reserve_ratio,
                futures_leverage=assumptions.futures_leverage,
                hedge_notional_ratio=hedge_ratio,
                capacity_spot_notional=capacity,
                policy=liquidity_policy,
                max_impact_bps=max_impact_bps,
            )
            evaluation = evaluate_cash_and_carry(
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

            if evaluation.gross_basis_return_on_notional <= 0:
                reasons.append("future_not_in_contango")
            if evaluation.expected_net_return_to_expiry <= 0:
                reasons.append("expected_net_return_not_positive")

            qualification = OpportunityQualification(
                qualified=not reasons,
                reasons=tuple(reasons),
            )
            key = (
                f"cash-and-carry:{snapshot.venue}:"
                f"{snapshot.spot_instrument_id}:{snapshot.future_instrument_id}"
            )

            opportunity = evolve_opportunity(
                await self.opportunities.get_active_by_key(key),
                opportunity_id=str(uuid4()),
                key=key,
                strategy_type=CASH_AND_CARRY.name,
                qualified=qualification.qualified,
                observed_at=snapshot.observed_at,
            )

            expected_cost = (
                evaluation.assumed_fee_return
                + evaluation.estimated_liquidity_cost_return
            )
            observation = OpportunityObservation(
                id=str(uuid4()),
                opportunity_id=opportunity.id,
                observed_at=snapshot.observed_at,
                return_estimate=ReturnEstimate(
                    character=ReturnCharacter.CONVERGENT,
                    expected_net_return=evaluation.expected_net_return_to_expiry,
                    annualized_equivalent=evaluation.annualized_equivalent,
                    expected_cost=expected_cost,
                ),
                capacity_5bps=evaluation.visible_capacity_5bps,
                capacity_10bps=evaluation.visible_capacity_10bps,
            )
            await self.opportunities.record(opportunity, observation)

            results.append(
                DiscoveredCashAndCarry(
                    snapshot=snapshot,
                    opportunity=opportunity,
                    observation=observation,
                    qualification=qualification,
                    evaluation=evaluation,
                    deployment=deployment,
                )
            )

        return tuple(results)
