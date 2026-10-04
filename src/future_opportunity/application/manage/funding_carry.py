from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from future_opportunity.application.ports import FundingCarryMarketDataPort
from future_opportunity.application.repositories import (
    SimulationRecord,
    SimulationRepository,
)
from future_opportunity.application.manage.valuation import assess_closeable_return
from future_opportunity.application.simulate.risk import build_paper_risk_report
from future_opportunity.domain.position.model import PositionState
from future_opportunity.domain.risk.model import InvariantState
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    evaluate_funding_carry,
)


@dataclass(frozen=True, slots=True)
class RefreshFundingCarry:
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
        valuation = assess_closeable_return(
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
