"""
Database configuration.

Reads DATABASE_URL from environment. Does not fail at import time —
only raises when a caller explicitly requests the URL and it is missing.
"""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def database_url_configured() -> bool:
    """Return True if DATABASE_URL is set in the environment."""
    url = os.environ.get("DATABASE_URL", "").strip()
    return len(url) > 0 and url != 'postgresql://USER:PASSWORD@HOST:PORT/DATABASE'


def get_database_url() -> str:
    """
    Return the DATABASE_URL from environment.

    Raises RuntimeError if not configured.
    Never prints or logs the URL itself.
    """
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url or url == 'postgresql://USER:PASSWORD@HOST:PORT/DATABASE':
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set it in your .env file. See .env.example for format."
        )
    return url
