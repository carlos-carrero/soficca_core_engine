"""
Async connection pool for Postgres/Supabase.

Usage:
    from db.pool import create_pool, get_pool, close_pool, check_connection

    # At app startup (optional, only when persistence is enabled):
    await create_pool()

    # Use pool:
    pool = get_pool()
    async with pool.acquire() as conn:
        ...

    # At app shutdown:
    await close_pool()

Does NOT connect at import time.
Does NOT break app startup if DATABASE_URL is absent.
"""

from __future__ import annotations

from typing import Optional

import asyncpg

from db.config import get_database_url


_pool: Optional[asyncpg.Pool] = None


async def create_pool(
    min_size: int = 2,
    max_size: int = 10,
) -> asyncpg.Pool:
    """
    Create the global asyncpg connection pool.

    Raises RuntimeError if DATABASE_URL is not configured.
    """
    global _pool
    if _pool is not None:
        return _pool

    dsn = get_database_url()
    _pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=min_size,
        max_size=max_size,
    )
    return _pool


def get_pool() -> asyncpg.Pool:
    """
    Return the current connection pool.

    Raises RuntimeError if pool has not been created yet.
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialized. "
            "Call `await create_pool()` first."
        )
    return _pool


async def close_pool() -> None:
    """Close the global connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def check_connection() -> dict:
    """
    Verify database connectivity by running SELECT 1.

    Returns dict with connection info (no secrets).
    Raises if connection fails.
    """
    dsn = get_database_url()
    conn = await asyncpg.connect(dsn=dsn)
    try:
        result = await conn.fetchval("SELECT 1")
        version = await conn.fetchval("SELECT version()")
        db_name = await conn.fetchval("SELECT current_database()")
        return {
            "status": "ok",
            "select_1": result,
            "database": db_name,
            "version_short": version.split(",")[0] if version else "unknown",
        }
    finally:
        await conn.close()
