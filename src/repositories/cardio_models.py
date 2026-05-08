"""
Pydantic models for Cardio Pilot repository layer.

Create models: used as input for write functions.
Row models: used as typed output from read functions.

All fields are aligned with migrations/001_cardio_pilot_initial_schema.sql.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Create (write) models ────────────────────────────────────────


class PilotSessionCreate(BaseModel):
    """Input for creating a pilot session."""

    model_config = ConfigDict(extra="forbid")

    label: Optional[str] = None
    mode: str = "local_browser_session"
    notes: Optional[str] = None
    environment: str = "development"
    created_by: Optional[str] = None


class PilotCaseCreate(BaseModel):
    """Input for creating a pilot case."""

    model_config = ConfigDict(extra="forbid")

    session_id: Optional[str] = None
    case_id: str
    source: str = "free_text"
    raw_narrative: str
    chief_complaint_summary: Optional[str] = None
    current_status: str = "pending_intake"
    final_route: Optional[str] = None
    decision_status: Optional[str] = None
    human_review_required: bool = True
    extraction_source: Optional[str] = None
    routing_source: Optional[str] = None
    is_simulated: bool = True
    contains_pii_warning: bool = False
    metadata_json: Optional[Dict[str, Any]] = None


class AIExtractionCreate(BaseModel):
    """Input for saving an AI extraction result."""

    model_config = ConfigDict(extra="forbid")

    case_id: str  # UUID of pilot_cases row
    extraction_id: str
    model: str
    extraction_source: str
    confidence: float
    structured_summary: Optional[str] = None
    fields_json: Dict[str, Any]
    field_evidence_json: Optional[List[Any]] = None
    missing_information_json: Optional[Dict[str, Any]] = None
    completion_questions_json: Optional[List[str]] = None
    quality_flags_json: Optional[List[str]] = None
    pii_warnings_json: Optional[List[str]] = None
    warnings_json: Optional[List[str]] = None
    unmapped_signals_json: Optional[List[str]] = None
    possible_conflicts_json: Optional[List[str]] = None
    raw_response_json: Optional[Dict[str, Any]] = None


class HumanCorrectionCreate(BaseModel):
    """Input for saving a human correction record."""

    model_config = ConfigDict(extra="forbid")

    case_id: str  # UUID of pilot_cases row
    human_edits_applied: bool = False
    fields_edited_count: int = 0
    diffs_json: Optional[List[Any]] = None
    final_structured_input_json: Dict[str, Any]
    reviewer_label: Optional[str] = None


class EngineReportCreate(BaseModel):
    """Input for saving a deterministic engine report."""

    model_config = ConfigDict(extra="forbid")

    case_id: str  # UUID of pilot_cases row
    route: Optional[str] = None
    decision_status: Optional[str] = None
    report_json: Dict[str, Any]
    engine_input_json: Dict[str, Any]
    safety_json: Optional[Dict[str, Any]] = None
    trace_json: Optional[Dict[str, Any]] = None
    activated_rules_json: Optional[List[str]] = None
    engine_version: Optional[str] = None
    ruleset_version: Optional[str] = None
    safety_policy_version: Optional[str] = None
    contract_version: Optional[str] = None


class AuditRecordCreate(BaseModel):
    """Input for saving an audit record."""

    model_config = ConfigDict(extra="forbid")

    case_id: str  # UUID of pilot_cases row
    audit_id: str
    audit_json: Dict[str, Any]
    markdown_snapshot: Optional[str] = None


class ReviewerFeedbackCreate(BaseModel):
    """Input for saving reviewer feedback."""

    model_config = ConfigDict(extra="forbid")

    case_id: str  # UUID of pilot_cases row
    reviewer_name: Optional[str] = None
    reviewer_role: Optional[str] = None
    route_appropriate: str
    usefulness_score: int = Field(..., ge=1, le=5)
    missing_info_surfaced: Optional[str] = None
    safety_flags_assessment: Optional[str] = None
    estimated_review_time_saved: Optional[str] = None
    useful_before_consultation: Optional[str] = None
    comments: Optional[str] = None


class SessionSummaryCreate(BaseModel):
    """Input for saving an aggregate session summary."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    summary_id: str
    metrics_json: Dict[str, Any]
    route_distribution_json: Optional[Dict[str, Any]] = None
    reviewer_metrics_json: Optional[Dict[str, Any]] = None
    workflow_impact_json: Optional[Dict[str, Any]] = None
    governance_metrics_json: Optional[Dict[str, Any]] = None
    safety_assertions_json: Optional[Dict[str, Any]] = None
    case_summaries_json: Optional[List[Any]] = None


# ── Row (read) models ────────────────────────────────────────────


class PilotSessionRow(BaseModel):
    """A pilot session as read from the database."""

    id: str
    created_at: datetime
    updated_at: datetime
    label: Optional[str] = None
    mode: str
    notes: Optional[str] = None
    environment: str
    created_by: Optional[str] = None


class PilotCaseRow(BaseModel):
    """A pilot case as read from the database."""

    id: str
    session_id: Optional[str] = None
    case_id: str
    created_at: datetime
    updated_at: datetime
    source: str
    raw_narrative: str
    chief_complaint_summary: Optional[str] = None
    current_status: str
    final_route: Optional[str] = None
    decision_status: Optional[str] = None
    human_review_required: bool
    extraction_source: Optional[str] = None
    routing_source: Optional[str] = None
    is_simulated: bool
    contains_pii_warning: bool
    metadata_json: Optional[Dict[str, Any]] = None


class CaseBundle(BaseModel):
    """
    Full case bundle: case + latest sub-resources.

    Used for reading a complete case with all associated data.
    """

    case: Dict[str, Any]
    ai_extraction: Optional[Dict[str, Any]] = None
    human_correction: Optional[Dict[str, Any]] = None
    engine_report: Optional[Dict[str, Any]] = None
    audit_record: Optional[Dict[str, Any]] = None
    reviewer_feedback: List[Dict[str, Any]] = Field(default_factory=list)
