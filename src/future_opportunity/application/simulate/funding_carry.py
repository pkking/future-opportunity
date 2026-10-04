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
from future_opportunity.application.repositories import (
    SimulationRecord,
    SimulationRepository,
)
from future_opportunity.application.simulate.risk import build_paper_risk_report
from future_opportunity.domain.execution.model import Execution, ExecutionState
from future_opportunity.domain.risk.model import RiskReport
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions
from future_opportunity.domain.strategy.model import StrategyPlan


@dataclass(frozen=True, slots=True)
class SimulatedFundingCarry:
    discovered: DiscoveredFundingCarry
    plan: StrategyPlan
    execution_record: Execution
    execution: PaperFundingCarryResult
    risk: RiskReport


@dataclass(frozen=True, slots=True)
class SimulateFundingCarry:
    discovery: DiscoverFundingCarry
    simulations: SimulationRepository

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
        paper_execution = execute_paper_funding_carry(
            position_id=str(uuid4()),
            strategy_plan_id=plan.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=assumptions,
        )
        risk = build_paper_risk_report(
            paper_execution.position,
            plan,
            expected_net_return=discovered.evaluation.expected_net_return_horizon,
            books={
                discovered.snapshot.spot_instrument_id: discovered.snapshot.spot_book,
                discovered.snapshot.perpetual_instrument_id: discovered.snapshot.perpetual_book,
            },
        )
        execution_record = Execution(
            id=str(uuid4()),
            strategy_plan_id=plan.id,
            state=ExecutionState.COMPLETED,
            mode="paper",
            started_at=min(fill.filled_at for fill in paper_execution.fills),
            finished_at=max(fill.filled_at for fill in paper_execution.fills),
            fills=paper_execution.fills,
        )
        await self.simulations.record(
            SimulationRecord(
                plan=plan,
                execution=execution_record,
                position=paper_execution.position,
                entry_return=paper_execution.entry_return,
                current_return=paper_execution.entry_return,
                risk=risk,
            )
        )
        return SimulatedFundingCarry(
            discovered=discovered,
            plan=plan,
            execution_record=execution_record,
            execution=paper_execution,
            risk=risk,
        )
