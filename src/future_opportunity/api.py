from dataclasses import asdict
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI, Query

from future_opportunity.adapters.exchanges.factory import funding_market_data_for
from future_opportunity.adapters.persistence.memory import MemoryOpportunityRepository
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.execute.paper_funding_carry import (
    execute_paper_funding_carry,
)
from future_opportunity.application.plan.funding_carry import build_funding_carry_plan
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    evaluate_funding_carry,
)


app = FastAPI(title="future-opportunity", version="0.1.0")
opportunity_repository = MemoryOpportunityRepository()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


def assumptions(
    spot_fee_bps: Decimal,
    perpetual_fee_bps: Decimal,
) -> FundingCarryAssumptions:
    return FundingCarryAssumptions(
        spot_taker_fee_bps=spot_fee_bps,
        perpetual_taker_fee_bps=perpetual_fee_bps,
    )


@app.get("/v1/opportunities/{venue}/funding-carry/{base}")
async def discover_funding_carry(
    venue: str,
    base: str,
    capital: Decimal = Query(default=Decimal(10_000), gt=0),
    spot_fee_bps: Decimal = Query(default=Decimal(10), ge=0),
    perpetual_fee_bps: Decimal = Query(default=Decimal(5), ge=0),
) -> dict[str, object]:
    use_case = DiscoverFundingCarry(
        funding_market_data_for(venue),
        opportunity_repository,
    )
    result = await use_case.execute(
        base=base,
        capital=capital,
        assumptions=assumptions(spot_fee_bps, perpetual_fee_bps),
    )
    return asdict(result)


@app.post("/v1/simulations/{venue}/funding-carry/{base}")
async def simulate_funding_carry(
    venue: str,
    base: str,
    capital: Decimal = Query(default=Decimal(10_000), gt=0),
    spot_fee_bps: Decimal = Query(default=Decimal(10), ge=0),
    perpetual_fee_bps: Decimal = Query(default=Decimal(5), ge=0),
) -> dict[str, object]:
    market_data = funding_market_data_for(venue)
    snapshot = await market_data.snapshot(base)
    configured = assumptions(spot_fee_bps, perpetual_fee_bps)
    evaluation = evaluate_funding_carry(snapshot, capital, configured)

    opportunity_observation_id = str(uuid4())
    plan = build_funding_carry_plan(
        plan_id=str(uuid4()),
        opportunity_observation_id=opportunity_observation_id,
        snapshot=snapshot,
        capital=capital,
        assumptions=configured,
    )
    execution = execute_paper_funding_carry(
        position_id=str(uuid4()),
        strategy_plan_id=plan.id,
        snapshot=snapshot,
        capital=capital,
        assumptions=configured,
    )
    delta = evaluate_delta_neutrality(execution.position, plan.max_delta_pct)

    return {
        "mode": "paper",
        "live_orders": False,
        "evaluation": asdict(evaluation),
        "plan": asdict(plan),
        "position": asdict(execution.position),
        "entry_cost": {
            "spot_fee": execution.spot_fee,
            "perpetual_fee": execution.perpetual_fee,
            "slippage_bps": execution.entry_slippage_bps,
        },
        "risk": asdict(delta),
    }
