from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import psycopg


@dataclass(frozen=True, slots=True)
class AppliedMigration:
    name: str
    checksum: str


def _checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()


def apply_migrations(
    dsn: str,
    migrations_dir: Path = Path("migrations"),
) -> tuple[AppliedMigration, ...]:
    """Apply ordered SQL migrations once and reject checksum drift."""
    paths = sorted(migrations_dir.glob("*.sql"))
    if not paths:
        raise ValueError(f"no migrations found in {migrations_dir}")

    applied_now: list[AppliedMigration] = []

    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        existing = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT name, checksum FROM schema_migrations"
            ).fetchall()
        }

        for path in paths:
            sql = path.read_text()
            checksum = _checksum(sql)
            previous = existing.get(path.name)
            if previous is not None:
                if previous != checksum:
                    raise RuntimeError(
                        f"migration checksum changed after apply: {path.name}"
                    )
                continue

            conn.execute(sql)
            conn.execute(
                """
                INSERT INTO schema_migrations (name, checksum)
                VALUES (%s, %s)
                """,
                (path.name, checksum),
            )
            applied_now.append(
                AppliedMigration(name=path.name, checksum=checksum)
            )

    return tuple(applied_now)
