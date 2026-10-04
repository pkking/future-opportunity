from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal
from uuid import uuid4

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from future_opportunity.application.repositories import (
    OpportunityRepository,
    SimulationRecord,
    SimulationRepository,
)
from future_opportunity.domain.execution.model import (
    Execution,
    ExecutionState,
    Fill,
    FillSource,
)
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
    OpportunityState,
)
from future_opportunity.domain.position.model import LegPosition, Position, PositionState
from future_opportunity.domain.returns.model import ReturnAttribution
from future_opportunity.domain.risk.model import (
    InvariantResult,
    InvariantState,
    RiskReport,
)
from future_opportunity.domain.strategy.model import (
    Money,
    PlanLeg,
    StrategyPlan,
    StrategyRef,
)


def _jsonable(value: object) -> object:
    return json.loads(json.dumps(value, default=str))


def _pool(
    dsn: str,
    min_size: int,
    max_size: int,
) -> AsyncConnectionPool:
    return AsyncConnectionPool(
        conninfo=dsn,
        min_size=min_size,
        max_size=max_size,
        open=False,
        kwargs={"row_factory": dict_row},
    )


class PostgresOpportunityRepository(OpportunityRepository):
    """PostgreSQL implementation matching the V0 migrations."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    @classmethod
    async def connect(
        cls,
        dsn: str,
        *,
        min_size: int = 1,
        max_size: int = 4,
    ) -> PostgresOpportunityRepository:
        pool = _pool(dsn, min_size, max_size)
        await pool.open()
        await pool.wait()
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def get_active_by_key(self, key: str) -> Opportunity | None:
        async with self._pool.connection() as conn:
            row = await (
                await conn.execute(
                    """
                    SELECT
                        id,
                        opportunity_key,
                        strategy_type,
                        state,
                        discovered_at,
                        qualified_at,
                        expired_at
                    FROM opportunities
                    WHERE opportunity_key = %s
                      AND expired_at IS NULL
                    ORDER BY discovered_at DESC
                    LIMIT 1
                    """,
                    (key,),
                )
            ).fetchone()

        if row is None:
            return None

        return Opportunity(
            id=str(row["id"]),
            key=row["opportunity_key"],
            strategy_type=row["strategy_type"],
            state=OpportunityState(row["state"]),
            discovered_at=row["discovered_at"],
            qualified_at=row["qualified_at"],
            expired_at=row["expired_at"],
        )

    async def record(
        self,
        opportunity: Opportunity,
        observation: OpportunityObservation,
    ) -> None:
        estimate = observation.return_estimate

        async with self._pool.connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO opportunities (
                        id,
                        opportunity_key,
                        strategy_type,
                        state,
                        discovered_at,
                        qualified_at,
                        expired_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET
                        state = EXCLUDED.state,
                        qualified_at = EXCLUDED.qualified_at,
                        expired_at = EXCLUDED.expired_at,
                        version = opportunities.version + 1
                    """,
                    (
                        opportunity.id,
                        opportunity.key,
                        opportunity.strategy_type,
                        opportunity.state.value,
                        opportunity.discovered_at,
                        opportunity.qualified_at,
                        opportunity.expired_at,
                    ),
                )
                await conn.execute(
                    """
                    INSERT INTO opportunity_observations (
                        id,
                        opportunity_id,
                        observed_at,
                        return_character,
                        expected_net_return,
                        annualized_equivalent,
                        expected_cost,
                        capacity_5bps,
                        capacity_10bps,
                        raw_metrics
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, '{}'::jsonb)
                    """,
                    (
                        observation.id,
                        observation.opportunity_id,
                        observation.observed_at,
                        estimate.character.value,
                        estimate.expected_net_return,
                        estimate.annualized_equivalent,
                        estimate.expected_cost,
                        observation.capacity_5bps,
                        observation.capacity_10bps,
                    ),
                )
                await conn.execute(
                    """
                    UPDATE opportunities
                    SET latest_observation_id = %s
                    WHERE id = %s
                    """,
                    (observation.id, opportunity.id),
                )


class PostgresSimulationRepository(SimulationRepository):
    """Atomic persistence for paper Plan -> Execution -> Position evidence."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    @classmethod
    async def connect(
        cls,
        dsn: str,
        *,
        min_size: int = 1,
        max_size: int = 4,
    ) -> PostgresSimulationRepository:
        pool = _pool(dsn, min_size, max_size)
        await pool.open()
        await pool.wait()
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def record(self, simulation: SimulationRecord) -> None:
        plan = simulation.plan
        execution = simulation.execution
        position = simulation.position
        attribution = simulation.entry_return

        async with self._pool.connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO strategy_plans (
                        id,
                        strategy_name,
                        strategy_version,
                        opportunity_observation_id,
                        venue,
                        base_asset,
                        quote_asset,
                        capital_amount,
                        capital_currency,
                        execution_mode,
                        current_revision
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                    """,
                    (
                        plan.id,
                        plan.strategy.name,
                        plan.strategy.version,
                        plan.opportunity_observation_id,
                        plan.venue,
                        plan.base,
                        plan.quote,
                        plan.capital.amount,
                        plan.capital.currency,
                        plan.execution_mode,
                    ),
                )
                await conn.execute(
                    """
                    INSERT INTO strategy_plan_revisions (
                        strategy_plan_id,
                        revision,
                        document
                    )
                    VALUES (%s, 1, %s)
                    """,
                    (
                        plan.id,
                        Jsonb(_jsonable(asdict(plan))),
                    ),
                )
                await conn.execute(
                    """
                    INSERT INTO executions (
                        id,
                        strategy_plan_id,
                        state,
                        mode,
                        started_at,
                        finished_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        execution.id,
                        execution.strategy_plan_id,
                        execution.state.value,
                        execution.mode,
                        execution.started_at,
                        execution.finished_at,
                    ),
                )

                for fill in execution.fills:
                    await conn.execute(
                        """
                        INSERT INTO fills (
                            id,
                            execution_id,
                            instrument_id,
                            side,
                            quantity,
                            price,
                            reference_price,
                            notional,
                            fee,
                            slippage_bps,
                            slippage_quote,
                            source,
                            filled_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(uuid4()),
                            execution.id,
                            fill.instrument_id,
                            fill.side,
                            fill.quantity,
                            fill.price,
                            fill.reference_price,
                            fill.notional,
                            fill.fee,
                            fill.slippage_bps,
                            fill.slippage_quote,
                            fill.source.value,
                            fill.filled_at,
                        ),
                    )

                await conn.execute(
                    """
                    INSERT INTO positions (
                        id,
                        strategy_plan_id,
                        state,
                        capital,
                        current_delta,
                        current_delta_pct,
                        realized_pnl,
                        unrealized_pnl,
                        opened_at,
                        closed_at,
                        version
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        position.id,
                        position.strategy_plan_id,
                        position.state.value,
                        plan.capital.amount,
                        position.delta_notional,
                        position.delta_pct,
                        position.realized_pnl,
                        position.unrealized_pnl,
                        position.opened_at,
                        position.closed_at,
                        position.version,
                    ),
                )

                for leg in position.legs:
                    await conn.execute(
                        """
                        INSERT INTO position_legs (
                            position_id,
                            instrument_id,
                            quantity,
                            notional
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            position.id,
                            leg.instrument_id,
                            leg.quantity,
                            leg.notional,
                        ),
                    )

                observed_at = execution.finished_at or execution.started_at
                await conn.execute(
                    """
                    INSERT INTO return_attributions (
                        id,
                        position_id,
                        observed_at,
                        funding,
                        basis_convergence,
                        trading_fees,
                        slippage,
                        rebalancing_cost,
                        residual_directional_pnl
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        position.id,
                        observed_at,
                        attribution.funding,
                        attribution.basis_convergence,
                        attribution.trading_fees,
                        attribution.slippage,
                        attribution.rebalancing_cost,
                        attribution.residual_directional_pnl,
                    ),
                )

                for invariant in simulation.risk.invariants:
                    await conn.execute(
                        """
                        INSERT INTO risk_observations (
                            id,
                            position_id,
                            observed_at,
                            invariant_name,
                            state,
                            observed,
                            limit_value,
                            explanation
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(uuid4()),
                            position.id,
                            observed_at,
                            invariant.name,
                            invariant.state.value,
                            Jsonb(_jsonable(invariant.observed)),
                            Jsonb(_jsonable(invariant.limit)),
                            (
                                Jsonb(_jsonable(invariant.explanation))
                                if invariant.explanation is not None
                                else None
                            ),
                        ),
                    )

    async def get(self, position_id: str) -> SimulationRecord | None:
        async with self._pool.connection() as conn:
            position_row = await (
                await conn.execute(
                    """
                    SELECT p.*, sp.strategy_name, sp.strategy_version,
                           sp.opportunity_observation_id,
                           sp.venue, sp.base_asset, sp.quote_asset,
                           sp.capital_amount, sp.capital_currency,
                           sp.execution_mode, spr.document
                    FROM positions p
                    JOIN strategy_plans sp ON sp.id = p.strategy_plan_id
                    JOIN strategy_plan_revisions spr
                      ON spr.strategy_plan_id = sp.id
                     AND spr.revision = sp.current_revision
                    WHERE p.id = %s
                    """,
                    (position_id,),
                )
            ).fetchone()

            if position_row is None:
                return None

            return await self._hydrate(conn, position_row)

    async def list(self) -> tuple[SimulationRecord, ...]:
        async with self._pool.connection() as conn:
            rows = await (
                await conn.execute(
                    """
                    SELECT p.*, sp.strategy_name, sp.strategy_version,
                           sp.opportunity_observation_id,
                           sp.venue, sp.base_asset, sp.quote_asset,
                           sp.capital_amount, sp.capital_currency,
                           sp.execution_mode, spr.document
                    FROM positions p
                    JOIN strategy_plans sp ON sp.id = p.strategy_plan_id
                    JOIN strategy_plan_revisions spr
                      ON spr.strategy_plan_id = sp.id
                     AND spr.revision = sp.current_revision
                    ORDER BY p.opened_at DESC NULLS LAST
                    """
                )
            ).fetchall()

            records = [await self._hydrate(conn, row) for row in rows]
            return tuple(records)

    async def _hydrate(self, conn: object, row: dict[str, object]) -> SimulationRecord:
        document = row["document"]
        legs_document = document["legs"]
        plan = StrategyPlan(
            id=str(row["strategy_plan_id"]),
            strategy=StrategyRef(
                name=row["strategy_name"],
                version=row["strategy_version"],
            ),
            opportunity_observation_id=str(row["opportunity_observation_id"]),
            venue=row["venue"],
            base=row["base_asset"],
            quote=row["quote_asset"],
            capital=Money(
                amount=Decimal(str(row["capital_amount"])),
                currency=row["capital_currency"],
            ),
            legs=tuple(
                PlanLeg(
                    id=leg["id"],
                    instrument_id=leg["instrument_id"],
                    side=leg["side"],
                    target_notional=Money(
                        amount=Decimal(str(leg["target_notional"]["amount"])),
                        currency=leg["target_notional"]["currency"],
                    ),
                )
                for leg in legs_document
            ),
            max_delta_pct=Decimal(str(document["max_delta_pct"])),
            max_leverage=Decimal(str(document["max_leverage"])),
            execution_mode=row["execution_mode"],
        )

        execution_row = await (
            await conn.execute(
                """
                SELECT *
                FROM executions
                WHERE strategy_plan_id = %s
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (plan.id,),
            )
        ).fetchone()
        fill_rows = await (
            await conn.execute(
                """
                SELECT *
                FROM fills
                WHERE execution_id = %s
                ORDER BY filled_at, instrument_id
                """,
                (execution_row["id"],),
            )
        ).fetchall()
        fills = tuple(
            Fill(
                instrument_id=fill["instrument_id"],
                side=fill["side"],
                quantity=fill["quantity"],
                price=fill["price"],
                reference_price=fill["reference_price"],
                notional=fill["notional"],
                fee=fill["fee"],
                slippage_bps=fill["slippage_bps"],
                slippage_quote=fill["slippage_quote"],
                filled_at=fill["filled_at"],
                source=FillSource(fill["source"]),
            )
            for fill in fill_rows
        )
        execution = Execution(
            id=str(execution_row["id"]),
            strategy_plan_id=str(execution_row["strategy_plan_id"]),
            state=ExecutionState(execution_row["state"]),
            mode=execution_row["mode"],
            started_at=execution_row["started_at"],
            finished_at=execution_row["finished_at"],
            fills=fills,
        )

        leg_rows = await (
            await conn.execute(
                """
                SELECT *
                FROM position_legs
                WHERE position_id = %s
                ORDER BY instrument_id
                """,
                (row["id"],),
            )
        ).fetchall()
        position = Position(
            id=str(row["id"]),
            strategy_plan_id=str(row["strategy_plan_id"]),
            state=PositionState(row["state"]),
            legs=tuple(
                LegPosition(
                    instrument_id=leg["instrument_id"],
                    quantity=leg["quantity"],
                    notional=leg["notional"],
                )
                for leg in leg_rows
            ),
            delta_notional=row["current_delta"],
            delta_pct=row["current_delta_pct"],
            realized_pnl=row["realized_pnl"],
            unrealized_pnl=row["unrealized_pnl"],
            opened_at=row["opened_at"],
            closed_at=row["closed_at"],
            version=row["version"],
        )

        return_row = await (
            await conn.execute(
                """
                SELECT *
                FROM return_attributions
                WHERE position_id = %s
                ORDER BY observed_at ASC
                LIMIT 1
                """,
                (row["id"],),
            )
        ).fetchone()
        attribution = ReturnAttribution(
            funding=return_row["funding"],
            basis_convergence=return_row["basis_convergence"],
            trading_fees=return_row["trading_fees"],
            slippage=return_row["slippage"],
            rebalancing_cost=return_row["rebalancing_cost"],
            residual_directional_pnl=return_row["residual_directional_pnl"],
        )

        risk_rows = await (
            await conn.execute(
                """
                SELECT DISTINCT ON (invariant_name)
                    invariant_name, state, observed, limit_value, explanation
                FROM risk_observations
                WHERE position_id = %s
                ORDER BY invariant_name, observed_at DESC
                """,
                (row["id"],),
            )
        ).fetchall()
        risk = RiskReport(
            invariants=tuple(
                InvariantResult(
                    name=risk_row["invariant_name"],
                    state=InvariantState(risk_row["state"]),
                    observed=risk_row["observed"],
                    limit=risk_row["limit_value"],
                    explanation=risk_row["explanation"],
                )
                for risk_row in risk_rows
            )
        )

        return SimulationRecord(
            plan=plan,
            execution=execution,
            position=position,
            entry_return=attribution,
            risk=risk,
        )
