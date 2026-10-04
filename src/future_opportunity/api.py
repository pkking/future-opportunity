from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from decimal import Decimal
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query, Request

from future_opportunity.adapters.exchanges.factory import (
    cash_and_carry_market_data_for,
    funding_market_data_for,
)
from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.application.simulate.cash_and_carry import (
    FutureInstrumentNotFound,
    SimulateCashAndCarry,
)
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
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
    app.state.simulation_repository = MemorySimulationRepository()
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
    simulation_repository = request.app.state.simulation_repository

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
        configured = funding_assumptions(
            spot_fee_bps,
            derivative_fee_bps,
            reserve_ratio,
            futures_leverage,
        )
        simulated = await SimulateFundingCarry(
            DiscoverFundingCarry(
                funding_market_data_for(venue),
                repository,
            ),
            simulation_repository,
        ).execute(
            base=base,
            capital=capital,
            assumptions=configured,
        )
        return {
            "mode": "paper",
            "live_orders": False,
            "opportunity": asdict(simulated.discovered.opportunity),
            "observation": asdict(simulated.discovered.observation),
            "evaluation": asdict(simulated.discovered.evaluation),
            "plan": asdict(simulated.plan),
            "position": asdict(simulated.execution.position),
            "fills": [asdict(fill) for fill in simulated.execution.fills],
            "return_attribution": asdict(simulated.execution.entry_return),
            "entry_cost": {
                "spot_fee": simulated.execution.spot_fee,
                "derivative_fee": simulated.execution.perpetual_fee,
                "slippage_bps": simulated.execution.entry_slippage_bps,
            },
            "risk": asdict(simulated.risk),
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
        try:
            simulated = await SimulateCashAndCarry(
                DiscoverCashAndCarry(
                    cash_and_carry_market_data_for(venue),
                    repository,
                ),
                simulation_repository,
            ).execute(
                base=base,
                future_instrument_id=future_instrument_id,
                capital=capital,
                assumptions=configured,
            )
        except FutureInstrumentNotFound as error:
            raise HTTPException(
                status_code=404,
                detail=f"future instrument not found: {error}",
            ) from error

        return {
            "mode": "paper",
            "live_orders": False,
            "opportunity": asdict(simulated.discovered.opportunity),
            "observation": asdict(simulated.discovered.observation),
            "evaluation": asdict(simulated.discovered.evaluation),
            "plan": asdict(simulated.plan),
            "position": asdict(simulated.execution.position),
            "fills": [asdict(fill) for fill in simulated.execution.fills],
            "return_attribution": asdict(simulated.execution.entry_return),
            "entry_cost": {
                "spot_fee": simulated.execution.spot_fee,
                "derivative_fee": simulated.execution.futures_fee,
                "slippage_bps": simulated.execution.entry_slippage_bps,
            },
            "risk": asdict(simulated.risk),
        }

    raise HTTPException(status_code=404, detail=f"unsupported strategy: {strategy}")
