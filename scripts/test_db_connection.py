"""
Database connection test for Soficca Cardio Pilot.

Verifies that DATABASE_URL is configured and that the database is reachable.

Usage:
    cd soficca_core_engine
    set PYTHONPATH=src
    python scripts/test_db_connection.py

Safety:
    - Never prints DATABASE_URL or secrets
    - Only runs SELECT 1 and metadata queries
"""

from __future__ import annotations

import asyncio
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

from db.config import database_url_configured
from db.pool import check_connection


async def main() -> None:
    print("Soficca Cardio Pilot — Database Connection Test")
    print("=" * 50)

    if not database_url_configured():
        print("\nERROR: DATABASE_URL is not configured.")
        print("Set it in your .env file. See .env.example for format.")
        sys.exit(1)

    print("\nDATABASE_URL is configured (value not printed).")
    print("Testing connection...")

    try:
        info = await check_connection()
    except Exception as e:
        print(f"\nERROR: Connection failed.")
        print(f"Details: {type(e).__name__}: {e}")
        print("\nCheck your DATABASE_URL in .env")
        sys.exit(1)

    print(f"\n✓ Database connection OK.")
    print(f"  Database: {info['database']}")
    print(f"  Provider: {info['version_short']}")
    print(f"  SELECT 1: {info['select_1']}")
    print(f"\nNo secrets printed.")


if __name__ == "__main__":
    asyncio.run(main())
