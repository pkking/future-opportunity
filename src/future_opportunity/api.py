from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from decimal import Decimal
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request

from future_opportunity.adapters.exchanges.factory import (
    cash_and_carry_market_data_for,
    funding_market_data_for,
)
from future_opportunity.adapters.persistence.memory import MemoryOpportunityRepository
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.execute.paper_cash_and_carry import (
    execute_paper_cash_and_carry,
)
from future_opportunity.application.execute.paper_funding_carry import (
    execute_paper_funding_carry,
)
from future_opportunity.application.plan.cash_and_carry import build_cash_and_carry_plan
from future_opportunity.application.plan.funding_carry import build_funding_carry_plan
from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.domain.risk.invariants import evaluate_delta_neutrality
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


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


def funding_assumptions(
    spot_fee_bps: Decimal,
    derivative_fee_bps: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
) -> FundingCarryAssumptions:
    return FundingCarryAssumptions(
        spot_taker_fee_bps=spot_fee_bps,
        perpetual_taker_fee_bps=derivative_fee_bps,
        reserve_ratio=reserve_ratio,
        futures_leverage=futures_leverage,
    )


def cash_assumptions(
    spot_fee_bps: Decimal,
    derivative_fee_bps: Decimal,
    reserve_ratio: Decimal,
    futures_leverage: Decimal,
    exit_buffer_bps: Decimal,
) -> CashAndCarryAssumptions:
    return CashAndCarryAssumptions(
        reserve_ratio=reserve_ratio,
        futures_leverage=futures_leverage,
        spot_entry_fee_bps=spot_fee_bps,
        spot_exit_fee_bps=spot_fee_bps,
        futures_entry_fee_bps=derivative_fee_bps,
        futures_settlement_fee_bps=derivative_fee_bps,
        exit_buffer_bps=exit_buffer_bps,
    )


def _discovery_view(result: object) -> dict[str, object]:
    return {
        "opportunity": asdict(result.opportunity),
        "observation": asdict(result.observation),
        "qualification": asdict(result.qualification),
        "evaluation": asdict(result.evaluation),
    }


@app.get("/v1/opportunities/{venue}/{strategy}/{base}")
async def discover(
    request: Request,
    venue: str,
    strategy: str,
    base: str,
    capital: Decimal = Query(default=Decimal(10_000), gt=0),
    spot_fee_bps: Decimal = Query(default=Decimal(10), ge=0),
    derivative_fee_bps: Decimal = Query(default=Decimal(5), ge=0),
    reserve_ratio: Decimal = Query(default=Decimal("0.10"), ge=0, lt=1),
    futures_leverage: Decimal = Query(default=Decimal(1), gt=0, le=Decimal("1.2")),
    exit_buffer_bps: Decimal = Query(default=Decimal(5), ge=0),
) -> dict[str, object]:
    repository: OpportunityRepository = request.app.state.opportunity_repository

    if strategy == "funding-carry":
        result = await DiscoverFundingCarry(
            funding_market_data_for(venue),
            repository,
        ).execute(
            base=base,
            capital=capital,
            assumptions=funding_assumptions(
                spot_fee_bps,
                derivative_fee_bps,
                reserve_ratio,
                futures_leverage,
            ),
        )
        return {
            "strategy": strategy,
            "venue": venue,
            "results": [_discovery_view(result)],
        }

    if strategy == "cash-and-carry":
        results = await DiscoverCashAndCarry(
            cash_and_carry_market_data_for(venue),
            repository,
        ).execute(
            base=base,
            capital=capital,
            assumptions=cash_assumptions(
                spot_fee_bps,
                derivative_fee_bps,
                reserve_ratio,
                futures_leverage,
                exit_buffer_bps,
            ),
        )
        return {
            "strategy": strategy,
            "venue": venue,
            "results": [_discovery_view(result) for result in results],
        }

    raise HTTPException(status_code=404, detail=f"unsupported strategy: {strategy}")


@app.post("/v1/simulations/{venue}/{strategy}/{base}")
async def simulate(
    request: Request,
    venue: str,
    strategy: str,
    base: str,
    capital: Decimal = Query(default=Decimal(10_000), gt=0),
    spot_fee_bps: Decimal = Query(default=Decimal(10), ge=0),
    derivative_fee_bps: Decimal = Query(default=Decimal(5), ge=0),
    reserve_ratio: Decimal = Query(default=Decimal("0.10"), ge=0, lt=1),
    futures_leverage: Decimal = Query(default=Decimal(1), gt=0, le=Decimal("1.2")),
    exit_buffer_bps: Decimal = Query(default=Decimal(5), ge=0),
    future_instrument_id: str | None = Query(default=None),
) -> dict[str, object]:
    repository: OpportunityRepository = request.app.state.opportunity_repository

    if strategy == "funding-carry":
        discovered = await DiscoverFundingCarry(
            funding_market_data_for(venue),
            repository,
        ).execute(
            base=base,
            capital=capital,
            assumptions=funding_assumptions(
                spot_fee_bps,
                derivative_fee_bps,
                reserve_ratio,
                futures_leverage,
            ),
        )
        configured = funding_assumptions(
            spot_fee_bps,
            derivative_fee_bps,
            reserve_ratio,
            futures_leverage,
        )
        plan = build_funding_carry_plan(
            plan_id=str(uuid4()),
            opportunity_observation_id=discovered.observation.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=configured,
        )
        execution = execute_paper_funding_carry(
            position_id=str(uuid4()),
            strategy_plan_id=plan.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=configured,
        )
        risk = evaluate_delta_neutrality(execution.position, plan.max_delta_pct)

        return {
            "mode": "paper",
            "live_orders": False,
            "opportunity": asdict(discovered.opportunity),
            "observation": asdict(discovered.observation),
            "evaluation": asdict(discovered.evaluation),
            "plan": asdict(plan),
            "position": asdict(execution.position),
            "entry_cost": {
                "spot_fee": execution.spot_fee,
                "derivative_fee": execution.perpetual_fee,
                "slippage_bps": execution.entry_slippage_bps,
            },
            "risk": asdict(risk),
        }

    if strategy == "cash-and-carry":
        if future_instrument_id is None:
            raise HTTPException(
                status_code=400,
                detail="future_instrument_id is required for cash-and-carry simulation",
            )

        configured = cash_assumptions(
            spot_fee_bps,
            derivative_fee_bps,
            reserve_ratio,
            futures_leverage,
            exit_buffer_bps,
        )
        candidates = await DiscoverCashAndCarry(
            cash_and_carry_market_data_for(venue),
            repository,
        ).execute(
            base=base,
            capital=capital,
            assumptions=configured,
        )
        discovered = next(
            (
                candidate
                for candidate in candidates
                if candidate.snapshot.future_instrument_id == future_instrument_id
            ),
            None,
        )
        if discovered is None:
            raise HTTPException(
                status_code=404,
                detail=f"future instrument not found: {future_instrument_id}",
            )

        plan = build_cash_and_carry_plan(
            plan_id=str(uuid4()),
            opportunity_observation_id=discovered.observation.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=configured,
        )
        execution = execute_paper_cash_and_carry(
            position_id=str(uuid4()),
            strategy_plan_id=plan.id,
            snapshot=discovered.snapshot,
            capital=capital,
            assumptions=configured,
        )
        risk = evaluate_delta_neutrality(execution.position, plan.max_delta_pct)

        return {
            "mode": "paper",
            "live_orders": False,
            "opportunity": asdict(discovered.opportunity),
            "observation": asdict(discovered.observation),
            "evaluation": asdict(discovered.evaluation),
            "plan": asdict(plan),
            "position": asdict(execution.position),
            "entry_cost": {
                "spot_fee": execution.spot_fee,
                "derivative_fee": execution.futures_fee,
                "slippage_bps": execution.entry_slippage_bps,
            },
            "risk": asdict(risk),
        }

    raise HTTPException(status_code=404, detail=f"unsupported strategy: {strategy}")
