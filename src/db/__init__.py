"""
Soficca Core Engine — Database module.

Provides async Postgres connection pool for Cardio Pilot persistence.
Does NOT connect automatically on import.
Existing endpoints work without DATABASE_URL configured.
"""

from db.config import get_database_url, database_url_configured
from db.pool import get_pool, create_pool, close_pool, check_connection

__all__ = [
    "get_database_url",
    "database_url_configured",
    "get_pool",
    "create_pool",
    "close_pool",
    "check_connection",
]
