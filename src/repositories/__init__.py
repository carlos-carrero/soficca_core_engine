"""
Soficca Core Engine — Repository layer.

Async database access functions for Cardio Pilot persistence.
Does NOT connect at import time.
"""

from repositories.cardio_models import (
    PilotSessionCreate,
    PilotCaseCreate,
    AIExtractionCreate,
    HumanCorrectionCreate,
    EngineReportCreate,
    AuditRecordCreate,
    ReviewerFeedbackCreate,
    SessionSummaryCreate,
    PilotSessionRow,
    PilotCaseRow,
    CaseBundle,
)
from repositories.errors import (
    DatabaseNotConfiguredError,
    RecordNotFoundError,
    DatabaseWriteError,
)

__all__ = [
    # Models
    "PilotSessionCreate",
    "PilotCaseCreate",
    "AIExtractionCreate",
    "HumanCorrectionCreate",
    "EngineReportCreate",
    "AuditRecordCreate",
    "ReviewerFeedbackCreate",
    "SessionSummaryCreate",
    "PilotSessionRow",
    "PilotCaseRow",
    "CaseBundle",
    # Errors
    "DatabaseNotConfiguredError",
    "RecordNotFoundError",
    "DatabaseWriteError",
]
