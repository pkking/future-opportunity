from __future__ import annotations

from dataclasses import dataclass, replace

from future_opportunity.application.manage.valuation import assess_closeable_return
from future_opportunity.application.ports import CashAndCarryMarketDataPort
from future_opportunity.application.repositories import (
    SimulationRecord,
    SimulationRepository,
)
from future_opportunity.application.simulate.risk import build_paper_risk_report
from future_opportunity.domain.position.model import PositionState
from future_opportunity.domain.risk.model import InvariantState
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
    evaluate_cash_and_carry,
)


@dataclass(frozen=True, slots=True)
class RefreshCashAndCarry:
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
            deployed_spot_notional=(
                record.plan.deployment.actual_spot_notional
                if record.plan.deployment is not None
                else None
            ),
        )
        books = {
            snapshot.spot_instrument_id: snapshot.spot_book,
            snapshot.future_instrument_id: snapshot.future_book,
        }
        valuation = assess_closeable_return(record, books)
        risk = build_paper_risk_report(
            record.position,
            record.plan,
            expected_net_return=evaluation.expected_net_return_to_expiry,
            books=books,
        )
        degraded = any(
            invariant.state is InvariantState.VIOLATED
            for invariant in risk.invariants
        )
        position = replace(
            record.position,
            state=PositionState.DEGRADED if degraded else PositionState.ACTIVE,
            unrealized_pnl=(
                valuation.attribution.net_pnl - record.position.realized_pnl
            ),
        )
        await self.simulations.update_position(
            position,
            valuation.attribution,
            risk,
            snapshot.observed_at,
        )
        refreshed = await self.simulations.get(position_id)
        if refreshed is None:
            raise RuntimeError(f"position disappeared after refresh: {position_id}")
        return refreshed
