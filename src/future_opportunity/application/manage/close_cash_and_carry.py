from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from uuid import uuid4

from future_opportunity.application.manage.valuation import simulate_close_evidence
from future_opportunity.application.ports import CashAndCarryMarketDataPort
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
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
    evaluate_cash_and_carry,
)


@dataclass(frozen=True, slots=True)
class CloseCashAndCarry:
    market_data: CashAndCarryMarketDataPort
    simulations: SimulationRepository

    async def execute(self, position_id: str) -> SimulationRecord:
        record = await self.simulations.get(position_id)
        if record is None:
            raise KeyError(position_id)
        if record.plan.strategy.name != "cash-and-carry":
            raise ValueError("position is not a cash-and-carry strategy")
        if record.position.state is PositionState.CLOSED:
            return record

        capital_policy = record.plan.capital_policy
        cost_policy = record.plan.execution_cost_policy
        if capital_policy is None or cost_policy is None:
            raise ValueError("strategy plan is missing frozen economics policies")

        future_leg = next(
            (leg for leg in record.plan.legs if leg.id == "future-leg"),
            None,
        )
        if future_leg is None:
            raise ValueError("cash-and-carry plan has no future leg")

        snapshots = await self.market_data.snapshots(
            record.plan.base,
            record.plan.quote,
        )
        snapshot = next(
            (
                candidate
                for candidate in snapshots
                if candidate.future_instrument_id == future_leg.instrument_id
            ),
            None,
        )
        if snapshot is None:
            raise ValueError(
                f"future instrument is no longer available: {future_leg.instrument_id}"
            )

        assumptions = CashAndCarryAssumptions(
            reserve_ratio=capital_policy.reserve_ratio,
            futures_leverage=capital_policy.futures_leverage,
            spot_entry_fee_bps=cost_policy.spot_entry_fee_bps,
            futures_entry_fee_bps=cost_policy.derivative_entry_fee_bps,
            spot_exit_fee_bps=cost_policy.spot_exit_fee_bps,
            futures_settlement_fee_bps=cost_policy.derivative_exit_fee_bps,
            exit_buffer_bps=cost_policy.exit_buffer_bps,
        )
        evaluation = evaluate_cash_and_carry(
            snapshot,
            record.plan.capital.amount,
            assumptions,
        )
        books = {
            snapshot.spot_instrument_id: snapshot.spot_book,
            snapshot.future_instrument_id: snapshot.future_book,
        }
        close_evidence = simulate_close_evidence(record, books)
        risk = build_paper_risk_report(
            record.position,
            record.plan,
            expected_net_return=evaluation.expected_net_return_to_expiry,
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
