"""
Tests for the Cardio Pilot repository layer.

These tests use mocked asyncpg pool/connection so they run without a real database.
No real Supabase connection required.
No secrets used.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from repositories.cardio_models import (
    AIExtractionCreate,
    AuditRecordCreate,
    CaseBundle,
    EngineReportCreate,
    HumanCorrectionCreate,
    PilotCaseCreate,
    PilotCaseRow,
    PilotSessionCreate,
    PilotSessionRow,
    ReviewerFeedbackCreate,
    SessionSummaryCreate,
)
from repositories.errors import (
    DatabaseNotConfiguredError,
    DatabaseWriteError,
    RecordNotFoundError,
)


# ── Model validation tests ───────────────────────────────────────


class TestModelValidation:
    """Verify Pydantic models accept valid data and reject bad data."""

    def test_pilot_session_create_defaults(self):
        data = PilotSessionCreate()
        assert data.mode == "local_browser_session"
        assert data.environment == "development"
        assert data.label is None

    def test_pilot_session_create_custom(self):
        data = PilotSessionCreate(
            label="Demo session 1",
            mode="controlled_pilot",
            environment="staging",
            created_by="test-user",
        )
        assert data.label == "Demo session 1"
        assert data.mode == "controlled_pilot"

    def test_pilot_case_create_required_fields(self):
        data = PilotCaseCreate(
            session_id=str(uuid4()),
            case_id="CP-TEST-001",
            raw_narrative="64-year-old with chest pain",
        )
        assert data.source == "free_text"
        assert data.is_simulated is True
        assert data.human_review_required is True

    def test_pilot_case_create_rejects_extra(self):
        with pytest.raises(Exception):
            PilotCaseCreate(
                session_id=str(uuid4()),
                case_id="CP-TEST-001",
                raw_narrative="test",
                nonexistent_field="bad",
            )

    def test_ai_extraction_create_fields_json_required(self):
        with pytest.raises(Exception):
            AIExtractionCreate(
                case_id=str(uuid4()),
                extraction_id="EXT-001",
                model="gpt-4o-mini",
                extraction_source="ai",
                confidence=0.85,
                # fields_json missing
            )

    def test_ai_extraction_create_valid(self):
        data = AIExtractionCreate(
            case_id=str(uuid4()),
            extraction_id="EXT-001",
            model="gpt-4o-mini",
            extraction_source="ai",
            confidence=0.85,
            fields_json={"age": 64, "chest_pain_present": True},
        )
        assert data.confidence == 0.85
        assert data.fields_json["age"] == 64

    def test_human_correction_create_valid(self):
        data = HumanCorrectionCreate(
            case_id=str(uuid4()),
            human_edits_applied=True,
            fields_edited_count=2,
            diffs_json=[{"field": "age", "old": 60, "new": 64}],
            final_structured_input_json={"age": 64, "chest_pain_present": True},
        )
        assert data.fields_edited_count == 2

    def test_engine_report_create_valid(self):
        data = EngineReportCreate(
            case_id=str(uuid4()),
            route="emergency_pathway",
            decision_status="routed",
            report_json={"decision": {}, "safety": {}},
            engine_input_json={"state": {}, "context": {}},
            engine_version="1.0.0",
        )
        assert data.route == "emergency_pathway"

    def test_audit_record_create_valid(self):
        data = AuditRecordCreate(
            case_id=str(uuid4()),
            audit_id="AUD-001",
            audit_json={"case_id": "test", "signals": []},
            markdown_snapshot="# Audit Report",
        )
        assert data.audit_id == "AUD-001"

    def test_reviewer_feedback_score_range(self):
        data = ReviewerFeedbackCreate(
            case_id=str(uuid4()),
            route_appropriate="agree",
            usefulness_score=4,
        )
        assert data.usefulness_score == 4

    def test_reviewer_feedback_score_out_of_range(self):
        with pytest.raises(Exception):
            ReviewerFeedbackCreate(
                case_id=str(uuid4()),
                route_appropriate="agree",
                usefulness_score=6,
            )

    def test_session_summary_create_valid(self):
        data = SessionSummaryCreate(
            session_id=str(uuid4()),
            summary_id="SUM-001",
            metrics_json={"cases_processed": 5},
        )
        assert data.metrics_json["cases_processed"] == 5


# ── JSONB serialization tests ────────────────────────────────────


class TestJsonbSerialization:
    """Verify _jsonb helper serializes values correctly."""

    def test_jsonb_none(self):
        from repositories.cardio_pilot_repository import _jsonb

        assert _jsonb(None) is None

    def test_jsonb_dict(self):
        from repositories.cardio_pilot_repository import _jsonb

        result = _jsonb({"age": 64, "pain": True})
        parsed = json.loads(result)
        assert parsed["age"] == 64
        assert parsed["pain"] is True

    def test_jsonb_list(self):
        from repositories.cardio_pilot_repository import _jsonb

        result = _jsonb(["flag_a", "flag_b"])
        parsed = json.loads(result)
        assert parsed == ["flag_a", "flag_b"]

    def test_jsonb_nested(self):
        from repositories.cardio_pilot_repository import _jsonb

        data = {
            "decision": {"path": "emergency", "status": "routed"},
            "safety": {"flags": ["red_flag_1"]},
        }
        result = _jsonb(data)
        parsed = json.loads(result)
        assert parsed["decision"]["path"] == "emergency"
        assert len(parsed["safety"]["flags"]) == 1

    def test_jsonb_datetime_fallback(self):
        from repositories.cardio_pilot_repository import _jsonb

        data = {"timestamp": datetime(2026, 5, 6, 12, 0, 0, tzinfo=timezone.utc)}
        result = _jsonb(data)
        parsed = json.loads(result)
        assert "2026" in parsed["timestamp"]


# ── Row conversion tests ────────────────────────────────────────


class TestRowConversion:
    """Verify _row_to_dict handles UUID and datetime conversion."""

    def test_row_to_dict_basic(self):
        from repositories.cardio_pilot_repository import _row_to_dict

        mock_row = MagicMock()
        mock_row.__iter__ = MagicMock(return_value=iter([("key", "value")]))
        mock_row.keys = MagicMock(return_value=["key"])
        mock_row.__getitem__ = MagicMock(return_value="value")

        # Use a simple dict-like mock
        class FakeRecord(dict):
            pass

        row = FakeRecord({"name": "test", "count": 42})
        result = _row_to_dict(row)
        assert result["name"] == "test"
        assert result["count"] == 42


# ── Error handling tests ─────────────────────────────────────────


class TestErrors:
    """Verify error types work correctly."""

    def test_database_not_configured(self):
        err = DatabaseNotConfiguredError()
        assert "not configured" in str(err)

    def test_database_not_configured_custom(self):
        err = DatabaseNotConfiguredError("Custom message")
        assert str(err) == "Custom message"

    def test_record_not_found(self):
        err = RecordNotFoundError("pilot_cases", "CP-001")
        assert "pilot_cases" in str(err)
        assert "CP-001" in str(err)
        assert err.table == "pilot_cases"
        assert err.identifier == "CP-001"

    def test_database_write_error(self):
        err = DatabaseWriteError("ai_extractions", "unique constraint")
        assert "ai_extractions" in str(err)
        assert "unique constraint" in str(err)
        assert err.table == "ai_extractions"


# ── Import safety tests ─────────────────────────────────────────


class TestImportSafety:
    """Verify no connection is made at import time."""

    def test_import_models_no_connection(self):
        """Importing models should not trigger any DB connection."""
        from repositories.cardio_models import (
            PilotSessionCreate,
            PilotCaseCreate,
            CaseBundle,
        )
        assert PilotSessionCreate is not None
        assert PilotCaseCreate is not None
        assert CaseBundle is not None

    def test_import_repository_no_connection(self):
        """Importing repository module should not trigger any DB connection."""
        from repositories import cardio_pilot_repository
        assert cardio_pilot_repository is not None

    def test_import_errors_no_connection(self):
        """Importing errors should not trigger any DB connection."""
        from repositories.errors import (
            DatabaseNotConfiguredError,
            RecordNotFoundError,
            DatabaseWriteError,
        )
        assert DatabaseNotConfiguredError is not None


# ── Mocked write function tests ──────────────────────────────────


class TestMockedWrites:
    """Test write functions with mocked pool."""

    @pytest.fixture
    def mock_pool(self):
        pool = AsyncMock()
        return pool

    @pytest.mark.asyncio
    async def test_create_session_calls_parameterized_sql(self, mock_pool):
        fake_row = {
            "id": uuid4(),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "label": "Test",
            "mode": "local_browser_session",
            "notes": None,
            "environment": "development",
            "created_by": None,
        }
        mock_pool.fetchrow = AsyncMock(return_value=FakeRecord(fake_row))

        with patch("repositories.cardio_pilot_repository.get_pool", return_value=mock_pool):
            from repositories.cardio_pilot_repository import create_pilot_session

            result = await create_pilot_session(PilotSessionCreate(label="Test"))

        mock_pool.fetchrow.assert_called_once()
        call_args = mock_pool.fetchrow.call_args
        sql = call_args[0][0]
        assert "INSERT INTO pilot_sessions" in sql
        assert "$1" in sql
        assert result["label"] == "Test"

    @pytest.mark.asyncio
    async def test_create_case_calls_parameterized_sql(self, mock_pool):
        sid = str(uuid4())
        fake_row = {
            "id": uuid4(),
            "session_id": uuid4(),
            "case_id": "CP-TEST-001",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "source": "free_text",
            "raw_narrative": "test narrative",
            "chief_complaint_summary": None,
            "current_status": "pending_intake",
            "final_route": None,
            "decision_status": None,
            "human_review_required": True,
            "extraction_source": None,
            "routing_source": None,
            "is_simulated": True,
            "contains_pii_warning": False,
            "metadata_json": {},
        }
        mock_pool.fetchrow = AsyncMock(return_value=FakeRecord(fake_row))

        with patch("repositories.cardio_pilot_repository.get_pool", return_value=mock_pool):
            from repositories.cardio_pilot_repository import create_pilot_case

            result = await create_pilot_case(PilotCaseCreate(
                session_id=sid,
                case_id="CP-TEST-001",
                raw_narrative="test narrative",
            ))

        sql = mock_pool.fetchrow.call_args[0][0]
        assert "INSERT INTO pilot_cases" in sql
        assert "$1" in sql
        assert result["case_id"] == "CP-TEST-001"

    @pytest.mark.asyncio
    async def test_save_extraction_serializes_jsonb(self, mock_pool):
        cid = str(uuid4())
        fake_row = {
            "id": uuid4(),
            "case_id": uuid4(),
            "extraction_id": "EXT-001",
            "model": "gpt-4o-mini",
            "extraction_source": "ai",
            "confidence": 0.85,
            "structured_summary": "Summary",
            "fields_json": {"age": 64},
            "field_evidence_json": [],
            "missing_information_json": {},
            "completion_questions_json": [],
            "quality_flags_json": [],
            "pii_warnings_json": [],
            "warnings_json": [],
            "unmapped_signals_json": [],
            "possible_conflicts_json": [],
            "raw_response_json": None,
            "created_at": datetime.now(timezone.utc),
        }
        mock_pool.fetchrow = AsyncMock(return_value=FakeRecord(fake_row))

        with patch("repositories.cardio_pilot_repository.get_pool", return_value=mock_pool):
            from repositories.cardio_pilot_repository import save_ai_extraction

            result = await save_ai_extraction(AIExtractionCreate(
                case_id=cid,
                extraction_id="EXT-001",
                model="gpt-4o-mini",
                extraction_source="ai",
                confidence=0.85,
                fields_json={"age": 64},
            ))

        sql = mock_pool.fetchrow.call_args[0][0]
        assert "INSERT INTO ai_extractions" in sql
        assert "::jsonb" in sql
        assert result["extraction_id"] == "EXT-001"

    @pytest.mark.asyncio
    async def test_write_error_wraps_exception(self, mock_pool):
        mock_pool.fetchrow = AsyncMock(side_effect=Exception("connection refused"))

        with patch("repositories.cardio_pilot_repository.get_pool", return_value=mock_pool):
            from repositories.cardio_pilot_repository import create_pilot_session

            with pytest.raises(DatabaseWriteError) as exc_info:
                await create_pilot_session(PilotSessionCreate(label="Fail"))

            assert "pilot_sessions" in str(exc_info.value)


# ── Mocked read function tests ──────────────────────────────────


class TestMockedReads:
    """Test read functions with mocked pool."""

    @pytest.fixture
    def mock_pool(self):
        pool = AsyncMock()
        return pool

    @pytest.mark.asyncio
    async def test_get_case_bundle_composes_structure(self, mock_pool):
        case_uuid = uuid4()
        now = datetime.now(timezone.utc)

        case_row = FakeRecord({
            "id": case_uuid,
            "session_id": uuid4(),
            "case_id": "CP-BUNDLE-001",
            "created_at": now,
            "updated_at": now,
            "source": "free_text",
            "raw_narrative": "test",
            "chief_complaint_summary": None,
            "current_status": "routed",
            "final_route": "emergency_pathway",
            "decision_status": "routed",
            "human_review_required": True,
            "extraction_source": "ai",
            "routing_source": "backend",
            "is_simulated": True,
            "contains_pii_warning": False,
            "metadata_json": {},
        })
        extraction_row = FakeRecord({
            "id": uuid4(),
            "case_id": case_uuid,
            "extraction_id": "EXT-001",
            "model": "gpt-4o-mini",
            "extraction_source": "ai",
            "confidence": 0.9,
            "structured_summary": "summary",
            "fields_json": {"age": 64},
            "field_evidence_json": [],
            "missing_information_json": {},
            "completion_questions_json": [],
            "quality_flags_json": [],
            "pii_warnings_json": [],
            "warnings_json": [],
            "unmapped_signals_json": [],
            "possible_conflicts_json": [],
            "raw_response_json": None,
            "created_at": now,
        })

        # Configure mock to return case on first call, extraction on second, etc.
        mock_pool.fetchrow = AsyncMock(side_effect=[
            case_row,       # case lookup
            extraction_row, # ai_extraction
            None,           # human_correction (none)
            None,           # engine_report (none)
            None,           # audit_record (none)
        ])
        mock_pool.fetch = AsyncMock(return_value=[])  # reviewer_feedback

        with patch("repositories.cardio_pilot_repository.get_pool", return_value=mock_pool):
            from repositories.cardio_pilot_repository import get_case_bundle

            bundle = await get_case_bundle("CP-BUNDLE-001")

        assert bundle is not None
        assert bundle["case"]["case_id"] == "CP-BUNDLE-001"
        assert bundle["ai_extraction"]["extraction_id"] == "EXT-001"
        assert bundle["human_correction"] is None
        assert bundle["engine_report"] is None
        assert bundle["reviewer_feedback"] == []

    @pytest.mark.asyncio
    async def test_get_case_bundle_returns_none_for_missing(self, mock_pool):
        mock_pool.fetchrow = AsyncMock(return_value=None)

        with patch("repositories.cardio_pilot_repository.get_pool", return_value=mock_pool):
            from repositories.cardio_pilot_repository import get_case_bundle

            result = await get_case_bundle("NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_sessions_returns_list(self, mock_pool):
        now = datetime.now(timezone.utc)
        rows = [
            FakeRecord({
                "id": uuid4(),
                "created_at": now,
                "updated_at": now,
                "label": f"Session {i}",
                "mode": "local_browser_session",
                "notes": None,
                "environment": "development",
                "created_by": None,
            })
            for i in range(3)
        ]
        mock_pool.fetch = AsyncMock(return_value=rows)

        with patch("repositories.cardio_pilot_repository.get_pool", return_value=mock_pool):
            from repositories.cardio_pilot_repository import list_pilot_sessions

            result = await list_pilot_sessions(limit=10)

        assert len(result) == 3
        assert result[0]["label"] == "Session 0"


# ── Helper for mocking asyncpg.Record ────────────────────────────


class FakeRecord(dict):
    """Dict subclass that mimics asyncpg.Record for testing."""
    pass
