from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.discover.funding_carry import (
    DiscoverFundingCarry,
    DiscoveredFundingCarry,
)
from future_opportunity.application.execute.paper_funding_carry import (
    PaperFundingCarryResult,
    execute_paper_funding_carry,
)
from future_opportunity.application.plan.funding_carry import build_funding_carry_plan
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.risk.model import InvariantResult
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions
from future_opportunity.domain.strategy.model import StrategyPlan


@dataclass(frozen=True, slots=True)
class SimulatedFundingCarry:
    discovered: DiscoveredFundingCarry
    plan: StrategyPlan
    execution: PaperFundingCarryResult
    delta_risk: InvariantResult


@dataclass(frozen=True, slots=True)
class SimulateFundingCarry:
    discovery: DiscoverFundingCarry

    async def execute(
        self,
        base: str,
        capital: Decimal,
        assumptions: FundingCarryAssumptions,
    ) -> SimulatedFundingCarry:
        discovered = await self.discovery.execute(base, capital, assumptions)
        plan = build_funding_carry_plan(
            plan_id=str(uuid4()),
            opportunity_observation_id=discovered.observation.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=assumptions,
        )
        execution = execute_paper_funding_carry(
            position_id=str(uuid4()),
            strategy_plan_id=plan.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=assumptions,
        )
        delta_risk = evaluate_delta_neutrality(
            execution.position,
            plan.max_delta_pct,
        )
        return SimulatedFundingCarry(
            discovered=discovered,
            plan=plan,
            execution=execution,
            delta_risk=delta_risk,
        )
