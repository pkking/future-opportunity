from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.ports import CashAndCarryMarketDataPort
from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
    OpportunityQualification,
    OpportunityState,
    ReturnCharacter,
    ReturnEstimate,
)
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


@dataclass(frozen=True, slots=True)
class DiscoverCashAndCarry:
    market_data: CashAndCarryMarketDataPort
    opportunities: OpportunityRepository

    async def execute(
        self,
        base: str,
        capital: Decimal,
        assumptions: CashAndCarryAssumptions,
    ) -> tuple[DiscoveredCashAndCarry, ...]:
        snapshots = await self.market_data.snapshots(base)
        results: list[DiscoveredCashAndCarry] = []

        for snapshot in snapshots:
            evaluation = evaluate_cash_and_carry(snapshot, capital, assumptions)
            reasons: list[str] = []

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

            opportunity = await self.opportunities.get_active_by_key(key)
            if opportunity is None:
                opportunity = Opportunity(
                    id=str(uuid4()),
                    key=key,
                    strategy_type="cash-and-carry",
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
            )
            await self.opportunities.record(opportunity, observation)

            results.append(
                DiscoveredCashAndCarry(
                    snapshot=snapshot,
                    opportunity=opportunity,
                    observation=observation,
                    qualification=qualification,
                    evaluation=evaluation,
                )
            )

        return tuple(results)
