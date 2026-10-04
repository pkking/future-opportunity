from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.manage.valuation import simulate_close_evidence
from future_opportunity.application.ports import FundingCarryMarketDataPort
from future_opportunity.application.repositories import (
    SimulationRecord,
    SimulationRepository,
)
from future_opportunity.application.simulate.risk import build_paper_risk_report
from future_opportunity.domain.execution.model import (
    Execution,
    ExecutionPurpose,
    ExecutionState,
)
from future_opportunity.domain.position.model import PositionState
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    evaluate_funding_carry,
)


@dataclass(frozen=True, slots=True)
class CloseFundingCarry:
    market_data: FundingCarryMarketDataPort
    simulations: SimulationRepository

    async def execute(self, position_id: str) -> SimulationRecord:
        record = await self.simulations.get(position_id)
        if record is None:
            raise KeyError(position_id)
        if record.plan.strategy.name != "funding-carry":
            raise ValueError("position is not a funding-carry strategy")
        if record.position.state is PositionState.CLOSED:
            return record

        capital_policy = record.plan.capital_policy
        cost_policy = record.plan.execution_cost_policy
        expected = record.plan.expected_economics
        if capital_policy is None or cost_policy is None or expected is None:
            raise ValueError("strategy plan is missing frozen economics policies")

        snapshot = await self.market_data.snapshot(
            record.plan.base,
            record.plan.quote,
        )
        assumptions = FundingCarryAssumptions(
            horizon_days=max(1, int(expected.horizon_days)),
            reserve_ratio=capital_policy.reserve_ratio,
            futures_leverage=capital_policy.futures_leverage,
            spot_taker_fee_bps=cost_policy.spot_entry_fee_bps,
            perpetual_taker_fee_bps=cost_policy.derivative_entry_fee_bps,
        )
        evaluation = evaluate_funding_carry(
            snapshot,
            record.plan.capital.amount,
            assumptions,
        )
        books = {
            snapshot.spot_instrument_id: snapshot.spot_book,
            snapshot.perpetual_instrument_id: snapshot.perpetual_book,
        }
        close_evidence = simulate_close_evidence(
            record,
            books,
            unassessed_components=("funding",),
        )
        risk = build_paper_risk_report(
            record.position,
            record.plan,
            expected_net_return=evaluation.expected_net_return_horizon,
            books=books,
        )

        started_at = min(fill.filled_at for fill in close_evidence.fills)
        finished_at = max(fill.filled_at for fill in close_evidence.fills)
        execution = Execution(
            id=str(uuid4()),
            strategy_plan_id=record.plan.id,
            state=ExecutionState.COMPLETED,
            mode="paper",
            started_at=started_at,
            finished_at=finished_at,
            fills=close_evidence.fills,
            purpose=ExecutionPurpose.CLOSE,
        )
        position = replace(
            record.position,
            state=PositionState.CLOSED,
            legs=(),
            delta_notional=Decimal(0),
            delta_pct=Decimal(0),
            realized_pnl=close_evidence.attribution.net_pnl,
            unrealized_pnl=Decimal(0),
            closed_at=finished_at,
        )
        await self.simulations.close_position(
            position,
            execution,
            close_evidence.attribution,
            risk,
            finished_at,
        )
        closed = await self.simulations.get(position_id)
        if closed is None:
            raise RuntimeError(f"position disappeared after close: {position_id}")
        return closed
