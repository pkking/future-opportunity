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
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.risk.model import InvariantResult
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.model import StrategyPlan


class FutureInstrumentNotFound(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SimulatedCashAndCarry:
    discovered: DiscoveredCashAndCarry
    plan: StrategyPlan
    execution: PaperCashAndCarryResult
    delta_risk: InvariantResult


@dataclass(frozen=True, slots=True)
class SimulateCashAndCarry:
    discovery: DiscoverCashAndCarry

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

        plan = build_cash_and_carry_plan(
            plan_id=str(uuid4()),
            opportunity_observation_id=discovered.observation.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=assumptions,
        )
        execution = execute_paper_cash_and_carry(
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
        return SimulatedCashAndCarry(
            discovered=discovered,
            plan=plan,
            execution=execution,
            delta_risk=delta_risk,
        )
