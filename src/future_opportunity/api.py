from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse

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
from future_opportunity.application.repositories import (
    OpportunityRepository,
    SimulationRecord,
    SimulationRepository,
)
from future_opportunity.application.manage.cash_and_carry import RefreshCashAndCarry
from future_opportunity.application.manage.close_cash_and_carry import CloseCashAndCarry
from future_opportunity.application.manage.close_funding_carry import CloseFundingCarry
from future_opportunity.application.manage.funding_carry import RefreshFundingCarry
from future_opportunity.application.simulate.cash_and_carry import (
    FutureInstrumentNotFound,
    SimulateCashAndCarry,
)
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.definition import STRATEGIES, strategy_definition
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    opportunity_repository: OpportunityRepository
    simulation_repository: SimulationRepository
    postgres_opportunities = None
    postgres_simulations = None

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        from future_opportunity.adapters.persistence.postgres import (
            PostgresOpportunityRepository,
            PostgresSimulationRepository,
        )

        postgres_opportunities = await PostgresOpportunityRepository.connect(database_url)
        postgres_simulations = await PostgresSimulationRepository.connect(database_url)
        opportunity_repository = postgres_opportunities
        simulation_repository = postgres_simulations
    else:
        opportunity_repository = MemoryOpportunityRepository()
        simulation_repository = MemorySimulationRepository()

    app.state.opportunity_repository = opportunity_repository
    app.state.simulation_repository = simulation_repository
    yield

    if postgres_opportunities is not None:
        await postgres_opportunities.close()
    if postgres_simulations is not None:
        await postgres_simulations.close()


app = FastAPI(
    title="future-opportunity",
    version="0.1.0",
    lifespan=lifespan,
)
WEB_ROOT = Path(__file__).with_name("web")




@app.get("/", include_in_schema=False)
def web_index() -> FileResponse:
    return FileResponse(WEB_ROOT / "index.html")


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




def _simulation_record_view(record: SimulationRecord) -> dict[str, object]:
    return {
        "plan": asdict(record.plan),
        "execution": asdict(record.execution),
        "position": asdict(record.position),
        "entry_return": asdict(record.entry_return),
        "current_return": asdict(record.current_return),
        "current_net_pnl": record.current_return.net_pnl,
        "return_complete": record.current_return.complete,
        "management_executions": [
            asdict(execution) for execution in record.management_executions
        ],
        "risk": asdict(record.risk),
    }


def _history_record_view(record: SimulationRecord) -> dict[str, object]:
    expected = record.plan.expected_economics
    current_net_pnl = record.current_return.net_pnl
    capital = record.plan.capital.amount
    current_return = current_net_pnl / capital if capital else Decimal(0)
    closed = record.position.state.value == "closed"
    complete = record.current_return.complete
    if closed:
        progress_state = "realized" if complete else "realized_partial"
    else:
        progress_state = "in_progress" if complete else "in_progress_partial"

    return {
        "position_id": record.position.id,
        "strategy": record.plan.strategy.name,
        "venue": record.plan.venue,
        "base": record.plan.base,
        "quote": record.plan.quote,
        "position_state": record.position.state.value,
        "progress_state": progress_state,
        "opened_at": record.position.opened_at,
        "closed_at": record.position.closed_at,
        "expected": (
            asdict(expected)
            if expected is not None
            else None
        ),
        "current": {
            "net_pnl": current_net_pnl,
            "net_return": current_return,
            "complete": complete,
            "unassessed_components": record.current_return.unassessed_components,
            "attribution": asdict(record.current_return),
        },
        "variance": (
            {
                "net_pnl": current_net_pnl - expected.expected_net_pnl,
                "net_return": current_return - expected.expected_net_return,
            }
            if expected is not None
            else None
        ),
    }




@app.get("/v1/strategies")
def list_strategies() -> dict[str, object]:
    return {
        "results": [
            asdict(definition)
            for definition in STRATEGIES.values()
        ]
    }


@app.get("/v1/strategies/{name}")
def get_strategy(name: str) -> dict[str, object]:
    try:
        definition = strategy_definition(name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return asdict(definition)


@app.get("/v1/history")
async def history(request: Request) -> dict[str, object]:
    repository: SimulationRepository = request.app.state.simulation_repository
    records = await repository.list()
    return {"results": [_history_record_view(record) for record in records]}


@app.get("/v1/positions")
async def list_positions(request: Request) -> dict[str, object]:
    repository: SimulationRepository = request.app.state.simulation_repository
    records = await repository.list()
    return {"results": [_simulation_record_view(record) for record in records]}


@app.post("/v1/positions/{position_id}/refresh")
async def refresh_position(
    request: Request,
    position_id: str,
) -> dict[str, object]:
    repository: SimulationRepository = request.app.state.simulation_repository
    record = await repository.get(position_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"position not found: {position_id}")

    try:
        if record.plan.strategy.name == "funding-carry":
            refreshed = await RefreshFundingCarry(
                funding_market_data_for(record.plan.venue),
                repository,
            ).execute(position_id)
        elif record.plan.strategy.name == "cash-and-carry":
            refreshed = await RefreshCashAndCarry(
                cash_and_carry_market_data_for(record.plan.venue),
                repository,
            ).execute(position_id)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported strategy: {record.plan.strategy.name}",
            )
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return _simulation_record_view(refreshed)


@app.post("/v1/positions/{position_id}/close")
async def close_position(
    request: Request,
    position_id: str,
) -> dict[str, object]:
    repository: SimulationRepository = request.app.state.simulation_repository
    record = await repository.get(position_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"position not found: {position_id}")

    try:
        if record.plan.strategy.name == "funding-carry":
            closed = await CloseFundingCarry(
                funding_market_data_for(record.plan.venue),
                repository,
            ).execute(position_id)
        elif record.plan.strategy.name == "cash-and-carry":
            closed = await CloseCashAndCarry(
                cash_and_carry_market_data_for(record.plan.venue),
                repository,
            ).execute(position_id)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported strategy: {record.plan.strategy.name}",
            )
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return _simulation_record_view(closed)


@app.get("/v1/positions/{position_id}")
async def get_position(
    request: Request,
    position_id: str,
) -> dict[str, object]:
    repository: SimulationRepository = request.app.state.simulation_repository
    record = await repository.get(position_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"position not found: {position_id}")
    return _simulation_record_view(record)


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
    simulation_repository: SimulationRepository = request.app.state.simulation_repository

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
