"""
Migration runner for Soficca Cardio Pilot.

Reads DATABASE_URL from environment, connects to Postgres,
and applies pending SQL migration files in order.

Usage:
    cd soficca_core_engine
    set PYTHONPATH=src
    python scripts/run_migrations.py

Requirements:
    - DATABASE_URL must be set in .env or environment
    - asyncpg must be installed
    - Migration files in migrations/ directory

Safety:
    - Never prints DATABASE_URL or secrets
    - Only applies migrations not yet recorded in schema_migrations
    - Runs each migration in a transaction
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path for db module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import asyncpg
from db.config import get_database_url


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


async def ensure_schema_migrations_table(conn: asyncpg.Connection) -> None:
    """Create schema_migrations table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     text        PRIMARY KEY,
            applied_at  timestamptz NOT NULL DEFAULT now()
        );
    """)


async def get_applied_migrations(conn: asyncpg.Connection) -> set:
    """Return set of already-applied migration versions."""
    rows = await conn.fetch("SELECT version FROM schema_migrations ORDER BY version")
    return {row["version"] for row in rows}


def get_migration_files() -> list[tuple[str, Path]]:
    """Return sorted list of (version, path) for .sql files in migrations/."""
    if not MIGRATIONS_DIR.exists():
        return []
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    result = []
    for f in files:
        # Version is filename without extension
        version = f.stem
        result.append((version, f))
    return result


async def run_migrations() -> None:
    """Connect to database and apply pending migrations."""
    print("Soficca Cardio Pilot — Migration Runner")
    print("=" * 50)

    try:
        dsn = get_database_url()
    except RuntimeError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    print("Connecting to database...")

    try:
        conn = await asyncpg.connect(dsn=dsn)
    except Exception as e:
        print(f"\nERROR: Could not connect to database.")
        print(f"Details: {type(e).__name__}: {e}")
        print("Check your DATABASE_URL in .env")
        sys.exit(1)

    try:
        await ensure_schema_migrations_table(conn)
        applied = await get_applied_migrations(conn)
        migrations = get_migration_files()

        if not migrations:
            print("\nNo migration files found in migrations/")
            return

        pending = [(v, p) for v, p in migrations if v not in applied]

        if not pending:
            print(f"\nAll {len(migrations)} migration(s) already applied. Nothing to do.")
            return

        print(f"\nFound {len(pending)} pending migration(s):")
        for version, path in pending:
            print(f"  • {version}")

        print()

        for version, path in pending:
            print(f"Applying: {version} ...")
            sql = path.read_text(encoding="utf-8")

            # Run migration in a transaction
            async with conn.transaction():
                await conn.execute(sql)

            print(f"  ✓ Applied: {version}")

        print(f"\nDone. {len(pending)} migration(s) applied successfully.")
        print("No secrets printed.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
