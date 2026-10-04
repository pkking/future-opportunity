from __future__ import annotations

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from future_opportunity.application.repositories import OpportunityRepository
from future_opportunity.domain.opportunity.model import (
    Opportunity,
    OpportunityObservation,
    OpportunityState,
)


class PostgresOpportunityRepository(OpportunityRepository):
    """PostgreSQL implementation matching migrations/0001_v0_core.sql."""

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
        pool = AsyncConnectionPool(
            conninfo=dsn,
            min_size=min_size,
            max_size=max_size,
            open=False,
            kwargs={"row_factory": dict_row},
        )
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
