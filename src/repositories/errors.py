"""
Repository error types.

Controlled exceptions for repository operations.
Never leak DATABASE_URL or secrets in error messages.
"""

from __future__ import annotations


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when DATABASE_URL is missing or invalid."""

    def __init__(self, message: str = "DATABASE_URL is not configured."):
        super().__init__(message)


class RecordNotFoundError(Exception):
    """Raised when a requested record does not exist."""

    def __init__(self, table: str, identifier: str):
        super().__init__(f"Record not found in {table}: {identifier}")
        self.table = table
        self.identifier = identifier


class DatabaseWriteError(Exception):
    """Raised when a database insert/update fails."""

    def __init__(self, table: str, message: str):
        super().__init__(f"Write failed for {table}: {message}")
        self.table = table
