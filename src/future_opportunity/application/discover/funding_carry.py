from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.application.ports import FundingCarryMarketDataPort
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    FundingCarryEvaluation,
    evaluate_funding_carry,
)


@dataclass(frozen=True, slots=True)
class DiscoverFundingCarry:
    market_data: FundingCarryMarketDataPort

    async def execute(
        self,
        base: str,
        capital: Decimal,
        assumptions: FundingCarryAssumptions,
    ) -> FundingCarryEvaluation:
        snapshot = await self.market_data.snapshot(base)
        return evaluate_funding_carry(snapshot, capital, assumptions)
