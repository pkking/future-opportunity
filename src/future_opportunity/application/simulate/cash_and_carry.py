from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.discover.cash_and_carry import (
    DiscoverCashAndCarry,
    DiscoveredCashAndCarry,
)
from future_opportunity.application.execute.paper_cash_and_carry import (
    PaperCashAndCarryResult,
    execute_paper_cash_and_carry,
)
from future_opportunity.application.plan.cash_and_carry import build_cash_and_carry_plan
from future_opportunity.application.repositories import (
    SimulationRecord,
    SimulationRepository,
)
from future_opportunity.application.simulate.risk import build_paper_risk_report
from future_opportunity.domain.execution.model import Execution, ExecutionState
from future_opportunity.domain.risk.model import RiskReport
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.model import ExpectedEconomics, StrategyPlan


class FutureInstrumentNotFound(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SimulatedCashAndCarry:
    discovered: DiscoveredCashAndCarry
    plan: StrategyPlan
    execution_record: Execution
    execution: PaperCashAndCarryResult
    risk: RiskReport


@dataclass(frozen=True, slots=True)
class SimulateCashAndCarry:
    discovery: DiscoverCashAndCarry
    simulations: SimulationRepository

    async def execute(
        self,
        base: str,
        future_instrument_id: str,
        capital: Decimal,
        assumptions: CashAndCarryAssumptions,
    ) -> SimulatedCashAndCarry:
        candidates = await self.discovery.execute(base, capital, assumptions)
        discovered = next(
            (
                candidate
                for candidate in candidates
                if candidate.snapshot.future_instrument_id == future_instrument_id
            ),
            None,
        )
        if discovered is None:
            raise FutureInstrumentNotFound(future_instrument_id)

        evaluation = discovered.evaluation
        expected_cost_return = (
            evaluation.assumed_fee_return
            + evaluation.estimated_liquidity_cost_return
        )
        expected = ExpectedEconomics(
            return_character=evaluation.return_character,
            horizon_type="expiry",
            horizon_days=evaluation.days_to_expiry,
            expected_net_return=evaluation.expected_net_return_to_expiry,
            annualized_equivalent=evaluation.annualized_equivalent,
            expected_cost_return=expected_cost_return,
            expected_net_pnl=capital * evaluation.expected_net_return_to_expiry,
            expected_cost_pnl=capital * expected_cost_return,
        )
        plan = build_cash_and_carry_plan(
            plan_id=str(uuid4()),
            opportunity_observation_id=discovered.observation.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=assumptions,
            expected_economics=expected,
        )
        paper_execution = execute_paper_cash_and_carry(
            position_id=str(uuid4()),
            strategy_plan_id=plan.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=assumptions,
        )
        risk = build_paper_risk_report(
            paper_execution.position,
            plan,
            expected_net_return=discovered.evaluation.expected_net_return_to_expiry,
            books={
                discovered.snapshot.spot_instrument_id: discovered.snapshot.spot_book,
                discovered.snapshot.future_instrument_id: discovered.snapshot.future_book,
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
        return SimulatedCashAndCarry(
            discovered=discovered,
            plan=plan,
            execution_record=execution_record,
            execution=paper_execution,
            risk=risk,
        )
