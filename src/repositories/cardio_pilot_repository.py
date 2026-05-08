"""
Cardio Pilot repository — async database access layer.

All functions use parameterized SQL via asyncpg.
JSONB payloads are serialized with json.dumps before insert.
No connection at import time.
Append-only for audit-relevant tables.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import asyncpg

from db.pool import get_pool
from repositories.cardio_models import (
    AIExtractionCreate,
    AuditRecordCreate,
    EngineReportCreate,
    HumanCorrectionCreate,
    PilotCaseCreate,
    PilotSessionCreate,
    ReviewerFeedbackCreate,
    SessionSummaryCreate,
)
from repositories.errors import DatabaseWriteError, RecordNotFoundError


# ── Helpers ──────────────────────────────────────────────────────


def _jsonb(value: Any) -> Optional[str]:
    """Serialize a value to JSON string for JSONB column, or None."""
    if value is None:
        return None
    return json.dumps(value, default=str)


def _row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
    """Convert an asyncpg Record to a plain dict with JSON-safe values."""
    d = dict(row)
    for key, val in d.items():
        # Convert UUID to string
        if hasattr(val, "hex") and hasattr(val, "int"):
            d[key] = str(val)
        # Convert datetime to ISO string
        elif hasattr(val, "isoformat"):
            d[key] = val.isoformat()
    return d


# ── Write functions ──────────────────────────────────────────────


async def create_pilot_session(data: PilotSessionCreate) -> Dict[str, Any]:
    """Create a new pilot session. Returns inserted row as dict."""
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO pilot_sessions (label, mode, notes, environment, created_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            data.label,
            data.mode,
            data.notes,
            data.environment,
            data.created_by,
        )
    except Exception as e:
        raise DatabaseWriteError("pilot_sessions", str(e)) from e
    return _row_to_dict(row)


async def create_pilot_case(data: PilotCaseCreate) -> Dict[str, Any]:
    """Create a new pilot case. Returns inserted row as dict."""
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO pilot_cases (
                session_id, case_id, source, raw_narrative,
                chief_complaint_summary, current_status, final_route,
                decision_status, human_review_required, extraction_source,
                routing_source, is_simulated, contains_pii_warning, metadata_json
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14::jsonb)
            RETURNING *
            """,
            data.session_id,
            data.case_id,
            data.source,
            data.raw_narrative,
            data.chief_complaint_summary,
            data.current_status,
            data.final_route,
            data.decision_status,
            data.human_review_required,
            data.extraction_source,
            data.routing_source,
            data.is_simulated,
            data.contains_pii_warning,
            _jsonb(data.metadata_json) or "{}",
        )
    except Exception as e:
        raise DatabaseWriteError("pilot_cases", str(e)) from e
    return _row_to_dict(row)


async def save_ai_extraction(data: AIExtractionCreate) -> Dict[str, Any]:
    """Save an AI extraction result (append-only). Returns inserted row."""
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO ai_extractions (
                case_id, extraction_id, model, extraction_source, confidence,
                structured_summary, fields_json, field_evidence_json,
                missing_information_json, completion_questions_json,
                quality_flags_json, pii_warnings_json, warnings_json,
                unmapped_signals_json, possible_conflicts_json, raw_response_json
            )
            VALUES (
                $1, $2, $3, $4, $5, $6,
                $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb,
                $11::jsonb, $12::jsonb, $13::jsonb, $14::jsonb,
                $15::jsonb, $16::jsonb
            )
            RETURNING *
            """,
            data.case_id,
            data.extraction_id,
            data.model,
            data.extraction_source,
            data.confidence,
            data.structured_summary,
            _jsonb(data.fields_json),
            _jsonb(data.field_evidence_json) or "[]",
            _jsonb(data.missing_information_json) or "{}",
            _jsonb(data.completion_questions_json) or "[]",
            _jsonb(data.quality_flags_json) or "[]",
            _jsonb(data.pii_warnings_json) or "[]",
            _jsonb(data.warnings_json) or "[]",
            _jsonb(data.unmapped_signals_json) or "[]",
            _jsonb(data.possible_conflicts_json) or "[]",
            _jsonb(data.raw_response_json),
        )
    except Exception as e:
        raise DatabaseWriteError("ai_extractions", str(e)) from e
    return _row_to_dict(row)


async def save_human_correction(data: HumanCorrectionCreate) -> Dict[str, Any]:
    """Save a human correction record (append-only). Returns inserted row."""
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO human_corrections (
                case_id, human_edits_applied, fields_edited_count,
                diffs_json, final_structured_input_json, reviewer_label
            )
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6)
            RETURNING *
            """,
            data.case_id,
            data.human_edits_applied,
            data.fields_edited_count,
            _jsonb(data.diffs_json) or "[]",
            _jsonb(data.final_structured_input_json),
            data.reviewer_label,
        )
    except Exception as e:
        raise DatabaseWriteError("human_corrections", str(e)) from e
    return _row_to_dict(row)


async def save_engine_report(data: EngineReportCreate) -> Dict[str, Any]:
    """Save a deterministic engine report (append-only). Returns inserted row."""
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO engine_reports (
                case_id, route, decision_status, report_json, engine_input_json,
                safety_json, trace_json, activated_rules_json,
                engine_version, ruleset_version, safety_policy_version, contract_version
            )
            VALUES (
                $1, $2, $3, $4::jsonb, $5::jsonb,
                $6::jsonb, $7::jsonb, $8::jsonb,
                $9, $10, $11, $12
            )
            RETURNING *
            """,
            data.case_id,
            data.route,
            data.decision_status,
            _jsonb(data.report_json),
            _jsonb(data.engine_input_json),
            _jsonb(data.safety_json),
            _jsonb(data.trace_json),
            _jsonb(data.activated_rules_json) or "[]",
            data.engine_version,
            data.ruleset_version,
            data.safety_policy_version,
            data.contract_version,
        )
    except Exception as e:
        raise DatabaseWriteError("engine_reports", str(e)) from e
    return _row_to_dict(row)


async def save_audit_record(data: AuditRecordCreate) -> Dict[str, Any]:
    """Save an audit record (append-only). Returns inserted row."""
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO audit_records (case_id, audit_id, audit_json, markdown_snapshot)
            VALUES ($1, $2, $3::jsonb, $4)
            RETURNING *
            """,
            data.case_id,
            data.audit_id,
            _jsonb(data.audit_json),
            data.markdown_snapshot,
        )
    except Exception as e:
        raise DatabaseWriteError("audit_records", str(e)) from e
    return _row_to_dict(row)


async def save_reviewer_feedback(data: ReviewerFeedbackCreate) -> Dict[str, Any]:
    """Save reviewer feedback (append-only). Returns inserted row."""
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO reviewer_feedback (
                case_id, reviewer_name, reviewer_role, route_appropriate,
                usefulness_score, missing_info_surfaced, safety_flags_assessment,
                estimated_review_time_saved, useful_before_consultation, comments
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
            """,
            data.case_id,
            data.reviewer_name,
            data.reviewer_role,
            data.route_appropriate,
            data.usefulness_score,
            data.missing_info_surfaced,
            data.safety_flags_assessment,
            data.estimated_review_time_saved,
            data.useful_before_consultation,
            data.comments,
        )
    except Exception as e:
        raise DatabaseWriteError("reviewer_feedback", str(e)) from e
    return _row_to_dict(row)


async def save_session_summary(data: SessionSummaryCreate) -> Dict[str, Any]:
    """Save a session summary (append-only). Returns inserted row."""
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO session_summaries (
                session_id, summary_id, metrics_json, route_distribution_json,
                reviewer_metrics_json, workflow_impact_json, governance_metrics_json,
                safety_assertions_json, case_summaries_json
            )
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb)
            RETURNING *
            """,
            data.session_id,
            data.summary_id,
            _jsonb(data.metrics_json),
            _jsonb(data.route_distribution_json),
            _jsonb(data.reviewer_metrics_json),
            _jsonb(data.workflow_impact_json),
            _jsonb(data.governance_metrics_json),
            _jsonb(data.safety_assertions_json),
            _jsonb(data.case_summaries_json),
        )
    except Exception as e:
        raise DatabaseWriteError("session_summaries", str(e)) from e
    return _row_to_dict(row)


# ── Update functions ─────────────────────────────────────────────


async def update_case_status(
    case_uuid: str,
    current_status: str,
    final_route: Optional[str] = None,
    decision_status: Optional[str] = None,
    extraction_source: Optional[str] = None,
    routing_source: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a pilot case status fields. Returns updated row."""
    pool = get_pool()
    row = await pool.fetchrow(
        """
        UPDATE pilot_cases
        SET current_status = $2,
            final_route = COALESCE($3, final_route),
            decision_status = COALESCE($4, decision_status),
            extraction_source = COALESCE($5, extraction_source),
            routing_source = COALESCE($6, routing_source)
        WHERE id = $1
        RETURNING *
        """,
        case_uuid,
        current_status,
        final_route,
        decision_status,
        extraction_source,
        routing_source,
    )
    if row is None:
        raise RecordNotFoundError("pilot_cases", case_uuid)
    return _row_to_dict(row)


# ── Read functions ───────────────────────────────────────────────


async def list_pilot_sessions(
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List pilot sessions, most recent first."""
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT * FROM pilot_sessions
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """,
        limit,
        offset,
    )
    return [_row_to_dict(r) for r in rows]


async def list_pilot_cases(
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List pilot cases, optionally filtered by session_id."""
    pool = get_pool()
    if session_id:
        rows = await pool.fetch(
            """
            SELECT * FROM pilot_cases
            WHERE session_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            session_id,
            limit,
            offset,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT * FROM pilot_cases
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )
    return [_row_to_dict(r) for r in rows]


async def get_pilot_case(case_id: str) -> Optional[Dict[str, Any]]:
    """Get a pilot case by application-level case_id. Returns None if not found."""
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM pilot_cases WHERE case_id = $1",
        case_id,
    )
    return _row_to_dict(row) if row else None


async def get_case_bundle(case_id: str) -> Optional[Dict[str, Any]]:
    """
    Get full case bundle by application-level case_id.

    Returns: {case, ai_extraction, human_correction, engine_report, audit_record, reviewer_feedback[]}
    Uses latest record (by created_at) for sub-resources.
    Returns None if case not found.
    """
    pool = get_pool()

    # Get the case
    case_row = await pool.fetchrow(
        "SELECT * FROM pilot_cases WHERE case_id = $1",
        case_id,
    )
    if case_row is None:
        return None

    case_uuid = case_row["id"]

    # Get latest AI extraction
    extraction_row = await pool.fetchrow(
        """
        SELECT * FROM ai_extractions
        WHERE case_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """,
        case_uuid,
    )

    # Get latest human correction
    correction_row = await pool.fetchrow(
        """
        SELECT * FROM human_corrections
        WHERE case_id = $1
        ORDER BY reviewed_at DESC
        LIMIT 1
        """,
        case_uuid,
    )

    # Get latest engine report
    report_row = await pool.fetchrow(
        """
        SELECT * FROM engine_reports
        WHERE case_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """,
        case_uuid,
    )

    # Get latest audit record
    audit_row = await pool.fetchrow(
        """
        SELECT * FROM audit_records
        WHERE case_id = $1
        ORDER BY generated_at DESC
        LIMIT 1
        """,
        case_uuid,
    )

    # Get all reviewer feedback (append-only, multiple possible)
    feedback_rows = await pool.fetch(
        """
        SELECT * FROM reviewer_feedback
        WHERE case_id = $1
        ORDER BY reviewed_at DESC
        """,
        case_uuid,
    )

    return {
        "case": _row_to_dict(case_row),
        "ai_extraction": _row_to_dict(extraction_row) if extraction_row else None,
        "human_correction": _row_to_dict(correction_row) if correction_row else None,
        "engine_report": _row_to_dict(report_row) if report_row else None,
        "audit_record": _row_to_dict(audit_row) if audit_row else None,
        "reviewer_feedback": [_row_to_dict(r) for r in feedback_rows],
    }


async def get_session_summary(session_id: str) -> Optional[Dict[str, Any]]:
    """Get latest session summary by session_id. Returns None if not found."""
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT * FROM session_summaries
        WHERE session_id = $1
        ORDER BY generated_at DESC
        LIMIT 1
        """,
        session_id,
    )
    return _row_to_dict(row) if row else None


async def get_session_cases(session_id: str) -> List[Dict[str, Any]]:
    """Get all cases in a session, most recent first."""
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT * FROM pilot_cases
        WHERE session_id = $1
        ORDER BY created_at DESC
        """,
        session_id,
    )
    return [_row_to_dict(r) for r in rows]
