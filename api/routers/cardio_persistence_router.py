"""
Cardio Pilot persistence endpoints.

These endpoints persist and read Cardio Pilot case data using the
repository layer over Postgres/Supabase.

They do NOT change AI extraction or deterministic routing behavior.
They do NOT require authentication (future stage).
They return 503 if DATABASE_URL is not configured.

Product boundary:
  AI structures the signal.
  Human confirms or corrects.
  Soficca governs the route.
  Physicians make the final decision.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from db.config import database_url_configured
from db.pool import create_pool, get_pool
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
from repositories.cardio_pilot_repository import (
    create_pilot_case,
    create_pilot_session,
    get_case_bundle,
    get_pilot_case,
    get_session_summary,
    list_pilot_cases,
    list_pilot_sessions,
    save_ai_extraction,
    save_audit_record,
    save_engine_report,
    save_human_correction,
    save_reviewer_feedback,
    save_session_summary,
    update_case_status,
)
from repositories.errors import DatabaseWriteError, RecordNotFoundError

router = APIRouter(prefix="/v1/cardio/pilot", tags=["cardio-pilot-persistence"])


# ── Helpers ──────────────────────────────────────────────────────


async def _ensure_pool() -> None:
    """Ensure DB pool is created. Raises 503 if DATABASE_URL missing."""
    if not database_url_configured():
        raise HTTPException(
            status_code=503,
            detail="Database is not configured. Set DATABASE_URL in backend .env.",
        )
    try:
        get_pool()
    except RuntimeError:
        await create_pool()


def _handle_write_error(e: DatabaseWriteError) -> HTTPException:
    """Map DatabaseWriteError to HTTP response."""
    msg = str(e).lower()
    is_conflict = any(kw in msg for kw in (
        "unique", "duplicate", "already exists", "uniqueviolation", "23505",
    ))
    if is_conflict:
        return HTTPException(status_code=409, detail=f"Conflict: {e.table} record already exists.")
    return HTTPException(status_code=500, detail=f"Database write failed for {e.table}.")


# ── Request / Response Models ────────────────────────────────────


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Optional[str] = None
    mode: str = "local_browser_session"
    notes: Optional[str] = None
    environment: str = "development"
    created_by: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session: Dict[str, Any]


class SessionListResponse(BaseModel):
    sessions: List[Dict[str, Any]]
    count: int


class AIExtractionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    model: str
    extraction_source: str = "ai"
    confidence: float = 0.0
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


class HumanCorrectionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    human_edits_applied: bool = False
    fields_edited_count: int = 0
    diffs_json: Optional[List[Any]] = None
    final_structured_input_json: Dict[str, Any]
    reviewer_label: Optional[str] = None


class EngineReportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


class AuditRecordPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    audit_json: Dict[str, Any]
    markdown_snapshot: Optional[str] = None


class ReviewerFeedbackPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_name: Optional[str] = None
    reviewer_role: Optional[str] = None
    route_appropriate: str
    usefulness_score: int = Field(..., ge=1, le=5)
    missing_info_surfaced: Optional[str] = None
    safety_flags_assessment: Optional[str] = None
    estimated_review_time_saved: Optional[str] = None
    useful_before_consultation: Optional[str] = None
    comments: Optional[str] = None


class PersistCaseBundleRequest(BaseModel):
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

    ai_extraction: Optional[AIExtractionPayload] = None
    human_correction: Optional[HumanCorrectionPayload] = None
    engine_report: Optional[EngineReportPayload] = None
    audit_record: Optional[AuditRecordPayload] = None
    reviewer_feedback: Optional[List[ReviewerFeedbackPayload]] = None


class PersistCaseBundleResponse(BaseModel):
    case_id: str
    case_uuid: str
    saved: Dict[str, bool]


class CaseListResponse(BaseModel):
    cases: List[Dict[str, Any]]
    count: int


class CaseBundleResponse(BaseModel):
    case: Dict[str, Any]
    ai_extraction: Optional[Dict[str, Any]] = None
    human_correction: Optional[Dict[str, Any]] = None
    engine_report: Optional[Dict[str, Any]] = None
    audit_record: Optional[Dict[str, Any]] = None
    reviewer_feedback: List[Dict[str, Any]] = Field(default_factory=list)


class ReviewerFeedbackResponse(BaseModel):
    feedback: Dict[str, Any]
    case_status_updated: bool = False


class SessionSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary_id: str
    metrics_json: Dict[str, Any]
    route_distribution_json: Optional[Dict[str, Any]] = None
    reviewer_metrics_json: Optional[Dict[str, Any]] = None
    workflow_impact_json: Optional[Dict[str, Any]] = None
    governance_metrics_json: Optional[Dict[str, Any]] = None
    safety_assertions_json: Optional[Dict[str, Any]] = None
    case_summaries_json: Optional[List[Any]] = None


class SessionSummaryResponse(BaseModel):
    summary: Dict[str, Any]


# ── Session endpoints ────────────────────────────────────────────


@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_session(payload: CreateSessionRequest) -> CreateSessionResponse:
    """Create a new persisted pilot session."""
    await _ensure_pool()
    try:
        session = await create_pilot_session(PilotSessionCreate(
            label=payload.label,
            mode=payload.mode,
            notes=payload.notes,
            environment=payload.environment,
            created_by=payload.created_by,
        ))
    except DatabaseWriteError as e:
        raise _handle_write_error(e)
    return CreateSessionResponse(session=session)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> SessionListResponse:
    """List persisted pilot sessions."""
    await _ensure_pool()
    sessions = await list_pilot_sessions(limit=limit, offset=offset)
    return SessionListResponse(sessions=sessions, count=len(sessions))


# ── Case endpoints ───────────────────────────────────────────────


@router.post("/cases", response_model=PersistCaseBundleResponse, status_code=201)
async def persist_case_bundle(payload: PersistCaseBundleRequest) -> PersistCaseBundleResponse:
    """
    Persist a complete or partial case bundle.

    Creates the pilot case and optionally saves nested sub-resources
    (extraction, correction, report, audit, feedback).
    Append-only for sub-resources.
    Returns 409 if case_id already exists.
    """
    await _ensure_pool()

    saved = {
        "case": False,
        "ai_extraction": False,
        "human_correction": False,
        "engine_report": False,
        "audit_record": False,
        "reviewer_feedback": False,
    }

    # Create the case
    try:
        case_row = await create_pilot_case(PilotCaseCreate(
            session_id=payload.session_id or None,
            case_id=payload.case_id,
            source=payload.source,
            raw_narrative=payload.raw_narrative,
            chief_complaint_summary=payload.chief_complaint_summary,
            current_status=payload.current_status,
            final_route=payload.final_route,
            decision_status=payload.decision_status,
            human_review_required=payload.human_review_required,
            extraction_source=payload.extraction_source,
            routing_source=payload.routing_source,
            is_simulated=payload.is_simulated,
            contains_pii_warning=payload.contains_pii_warning,
            metadata_json=payload.metadata_json,
        ))
    except DatabaseWriteError as e:
        raise _handle_write_error(e)

    saved["case"] = True
    case_uuid = case_row["id"]

    # Save nested sub-resources
    if payload.ai_extraction:
        ext = payload.ai_extraction
        try:
            await save_ai_extraction(AIExtractionCreate(
                case_id=case_uuid,
                extraction_id=ext.extraction_id,
                model=ext.model,
                extraction_source=ext.extraction_source,
                confidence=ext.confidence,
                structured_summary=ext.structured_summary,
                fields_json=ext.fields_json,
                field_evidence_json=ext.field_evidence_json,
                missing_information_json=ext.missing_information_json,
                completion_questions_json=ext.completion_questions_json,
                quality_flags_json=ext.quality_flags_json,
                pii_warnings_json=ext.pii_warnings_json,
                warnings_json=ext.warnings_json,
                unmapped_signals_json=ext.unmapped_signals_json,
                possible_conflicts_json=ext.possible_conflicts_json,
                raw_response_json=ext.raw_response_json,
            ))
            saved["ai_extraction"] = True
        except DatabaseWriteError:
            pass  # Case created but sub-resource failed — non-fatal

    if payload.human_correction:
        hc = payload.human_correction
        try:
            await save_human_correction(HumanCorrectionCreate(
                case_id=case_uuid,
                human_edits_applied=hc.human_edits_applied,
                fields_edited_count=hc.fields_edited_count,
                diffs_json=hc.diffs_json,
                final_structured_input_json=hc.final_structured_input_json,
                reviewer_label=hc.reviewer_label,
            ))
            saved["human_correction"] = True
        except DatabaseWriteError:
            pass

    if payload.engine_report:
        er = payload.engine_report
        try:
            await save_engine_report(EngineReportCreate(
                case_id=case_uuid,
                route=er.route,
                decision_status=er.decision_status,
                report_json=er.report_json,
                engine_input_json=er.engine_input_json,
                safety_json=er.safety_json,
                trace_json=er.trace_json,
                activated_rules_json=er.activated_rules_json,
                engine_version=er.engine_version,
                ruleset_version=er.ruleset_version,
                safety_policy_version=er.safety_policy_version,
                contract_version=er.contract_version,
            ))
            saved["engine_report"] = True
        except DatabaseWriteError:
            pass

    if payload.audit_record:
        ar = payload.audit_record
        try:
            await save_audit_record(AuditRecordCreate(
                case_id=case_uuid,
                audit_id=ar.audit_id,
                audit_json=ar.audit_json,
                markdown_snapshot=ar.markdown_snapshot,
            ))
            saved["audit_record"] = True
        except DatabaseWriteError:
            pass

    if payload.reviewer_feedback:
        any_saved = False
        for fb in payload.reviewer_feedback:
            try:
                await save_reviewer_feedback(ReviewerFeedbackCreate(
                    case_id=case_uuid,
                    reviewer_name=fb.reviewer_name,
                    reviewer_role=fb.reviewer_role,
                    route_appropriate=fb.route_appropriate,
                    usefulness_score=fb.usefulness_score,
                    missing_info_surfaced=fb.missing_info_surfaced,
                    safety_flags_assessment=fb.safety_flags_assessment,
                    estimated_review_time_saved=fb.estimated_review_time_saved,
                    useful_before_consultation=fb.useful_before_consultation,
                    comments=fb.comments,
                ))
                any_saved = True
            except DatabaseWriteError:
                pass
        saved["reviewer_feedback"] = any_saved

    return PersistCaseBundleResponse(
        case_id=payload.case_id,
        case_uuid=case_uuid,
        saved=saved,
    )


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    session_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CaseListResponse:
    """List persisted pilot cases."""
    await _ensure_pool()
    cases = await list_pilot_cases(session_id=session_id, limit=limit, offset=offset)
    return CaseListResponse(cases=cases, count=len(cases))


@router.get("/cases/{case_id}", response_model=CaseBundleResponse)
async def read_case_bundle(case_id: str) -> CaseBundleResponse:
    """Read full persisted case bundle by application-level case_id."""
    await _ensure_pool()
    bundle = await get_case_bundle(case_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return CaseBundleResponse(**bundle)


# ── Reviewer feedback endpoint ───────────────────────────────────


@router.post("/cases/{case_id}/review", response_model=ReviewerFeedbackResponse, status_code=201)
async def add_reviewer_feedback(case_id: str, payload: ReviewerFeedbackPayload) -> ReviewerFeedbackResponse:
    """
    Add reviewer feedback for a persisted case.

    Verifies case exists, saves feedback, optionally updates case status.
    """
    await _ensure_pool()

    # Verify case exists
    case = await get_pilot_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    case_uuid = case["id"]

    try:
        feedback = await save_reviewer_feedback(ReviewerFeedbackCreate(
            case_id=case_uuid,
            reviewer_name=payload.reviewer_name,
            reviewer_role=payload.reviewer_role,
            route_appropriate=payload.route_appropriate,
            usefulness_score=payload.usefulness_score,
            missing_info_surfaced=payload.missing_info_surfaced,
            safety_flags_assessment=payload.safety_flags_assessment,
            estimated_review_time_saved=payload.estimated_review_time_saved,
            useful_before_consultation=payload.useful_before_consultation,
            comments=payload.comments,
        ))
    except DatabaseWriteError as e:
        raise _handle_write_error(e)

    # Update case status to reviewed
    status_updated = False
    try:
        await update_case_status(case_uuid, "reviewed")
        status_updated = True
    except (RecordNotFoundError, Exception):
        pass  # Non-fatal — feedback saved even if status update fails

    return ReviewerFeedbackResponse(feedback=feedback, case_status_updated=status_updated)


# ── Session summary endpoints ────────────────────────────────────


@router.post(
    "/sessions/{session_id}/summary",
    response_model=SessionSummaryResponse,
    status_code=201,
)
async def save_summary(session_id: str, payload: SessionSummaryRequest) -> SessionSummaryResponse:
    """Save an aggregate session summary."""
    await _ensure_pool()
    try:
        summary = await save_session_summary(SessionSummaryCreate(
            session_id=session_id,
            summary_id=payload.summary_id,
            metrics_json=payload.metrics_json,
            route_distribution_json=payload.route_distribution_json,
            reviewer_metrics_json=payload.reviewer_metrics_json,
            workflow_impact_json=payload.workflow_impact_json,
            governance_metrics_json=payload.governance_metrics_json,
            safety_assertions_json=payload.safety_assertions_json,
            case_summaries_json=payload.case_summaries_json,
        ))
    except DatabaseWriteError as e:
        raise _handle_write_error(e)
    return SessionSummaryResponse(summary=summary)


@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def read_summary(session_id: str) -> SessionSummaryResponse:
    """Get latest persisted session summary."""
    await _ensure_pool()
    summary = await get_session_summary(session_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"No summary found for session: {session_id}")
    return SessionSummaryResponse(summary=summary)
