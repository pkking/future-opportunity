from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from decimal import Decimal
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Query, Request

from future_opportunity.adapters.exchanges.factory import funding_market_data_for
from future_opportunity.adapters.persistence.memory import MemoryOpportunityRepository
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.execute.paper_funding_carry import (
    execute_paper_funding_carry,
)
from future_opportunity.application.plan.funding_carry import build_funding_carry_plan
from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    evaluate_funding_carry,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    repository: OpportunityRepository
    postgres_repository = None

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        from future_opportunity.adapters.persistence.postgres import (
            PostgresOpportunityRepository,
        )

        postgres_repository = await PostgresOpportunityRepository.connect(database_url)
        repository = postgres_repository
    else:
        repository = MemoryOpportunityRepository()

    app.state.opportunity_repository = repository
    yield

    if postgres_repository is not None:
        await postgres_repository.close()


app = FastAPI(
    title="future-opportunity",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


def assumptions(
    spot_fee_bps: Decimal,
    perpetual_fee_bps: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
) -> FundingCarryAssumptions:
    return FundingCarryAssumptions(
        spot_taker_fee_bps=spot_fee_bps,
        perpetual_taker_fee_bps=perpetual_fee_bps,
        reserve_ratio=reserve_ratio,
        futures_leverage=futures_leverage,
    )


@app.get("/v1/opportunities/{venue}/funding-carry/{base}")
async def discover_funding_carry(
    request: Request,
    venue: str,
    base: str,
    capital: Decimal = Query(default=Decimal(10_000), gt=0),
    spot_fee_bps: Decimal = Query(default=Decimal(10), ge=0),
    perpetual_fee_bps: Decimal = Query(default=Decimal(5), ge=0),
    reserve_ratio: Decimal = Query(default=Decimal("0.10"), ge=0, lt=1),
    futures_leverage: Decimal = Query(default=Decimal(1), gt=0, le=Decimal("1.2")),
) -> dict[str, object]:
    repository: OpportunityRepository = request.app.state.opportunity_repository
    use_case = DiscoverFundingCarry(
        funding_market_data_for(venue),
        repository,
    )
    result = await use_case.execute(
        base=base,
        capital=capital,
        assumptions=assumptions(
            spot_fee_bps,
            perpetual_fee_bps,
            reserve_ratio,
            futures_leverage,
        ),
    )
    return asdict(result)


@app.post("/v1/simulations/{venue}/funding-carry/{base}")
async def simulate_funding_carry(
    venue: str,
    base: str,
    capital: Decimal = Query(default=Decimal(10_000), gt=0),
    spot_fee_bps: Decimal = Query(default=Decimal(10), ge=0),
    perpetual_fee_bps: Decimal = Query(default=Decimal(5), ge=0),
    reserve_ratio: Decimal = Query(default=Decimal("0.10"), ge=0, lt=1),
    futures_leverage: Decimal = Query(default=Decimal(1), gt=0, le=Decimal("1.2")),
) -> dict[str, object]:
    market_data = funding_market_data_for(venue)
    snapshot = await market_data.snapshot(base)
    configured = assumptions(
        spot_fee_bps,
        perpetual_fee_bps,
        reserve_ratio,
        futures_leverage,
    )
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
