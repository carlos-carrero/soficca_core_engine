"""
Tests for Cardio Pilot persistence endpoints (Stage 3D).

Uses mocked repository functions — no real database required.
Existing /extract and /report endpoints remain unaffected.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ── Fixtures ─────────────────────────────────────────────────────


MOCK_SESSION = {
    "id": str(uuid4()),
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "label": "Test Session",
    "mode": "local_browser_session",
    "notes": None,
    "environment": "development",
    "created_by": None,
}

MOCK_CASE_UUID = str(uuid4())
MOCK_CASE = {
    "id": MOCK_CASE_UUID,
    "session_id": MOCK_SESSION["id"],
    "case_id": "CP-TEST-001",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "source": "free_text",
    "raw_narrative": "64-year-old with chest pain",
    "chief_complaint_summary": "Chest pain",
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

MOCK_EXTRACTION = {
    "id": str(uuid4()),
    "case_id": MOCK_CASE_UUID,
    "extraction_id": "EXT-001",
    "model": "gpt-4o-mini",
    "extraction_source": "ai",
    "confidence": 0.9,
    "structured_summary": "Summary",
    "fields_json": {"age": 64},
    "created_at": datetime.now(timezone.utc).isoformat(),
}

MOCK_FEEDBACK = {
    "id": str(uuid4()),
    "case_id": MOCK_CASE_UUID,
    "reviewer_name": "Dr. Test",
    "reviewer_role": "cardiologist",
    "route_appropriate": "agree",
    "usefulness_score": 4,
    "missing_info_surfaced": None,
    "safety_flags_assessment": None,
    "estimated_review_time_saved": None,
    "useful_before_consultation": None,
    "comments": "Good",
    "reviewed_at": datetime.now(timezone.utc).isoformat(),
}

MOCK_SUMMARY = {
    "id": str(uuid4()),
    "session_id": MOCK_SESSION["id"],
    "summary_id": "SUM-001",
    "metrics_json": {"cases_processed": 5},
    "generated_at": datetime.now(timezone.utc).isoformat(),
}

MOCK_BUNDLE = {
    "case": MOCK_CASE,
    "ai_extraction": MOCK_EXTRACTION,
    "human_correction": None,
    "engine_report": None,
    "audit_record": None,
    "reviewer_feedback": [MOCK_FEEDBACK],
}


def _db_configured():
    return True


def _db_not_configured():
    return False


# ── Session endpoint tests ───────────────────────────────────────


class TestSessionEndpoints:

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.create_pilot_session", new_callable=AsyncMock)
    def test_create_session(self, mock_create, mock_pool):
        mock_create.return_value = MOCK_SESSION
        resp = client.post("/v1/cardio/pilot/sessions", json={
            "label": "Test Session",
            "mode": "local_browser_session",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "session" in data
        assert data["session"]["label"] == "Test Session"

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.list_pilot_sessions", new_callable=AsyncMock)
    def test_list_sessions(self, mock_list, mock_pool):
        mock_list.return_value = [MOCK_SESSION]
        resp = client.get("/v1/cardio/pilot/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert len(data["sessions"]) == 1


# ── Case endpoint tests ─────────────────────────────────────────


class TestCaseEndpoints:

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.create_pilot_case", new_callable=AsyncMock)
    def test_persist_case_minimal(self, mock_create, mock_pool):
        mock_create.return_value = MOCK_CASE
        resp = client.post("/v1/cardio/pilot/cases", json={
            "case_id": "CP-TEST-001",
            "raw_narrative": "64-year-old with chest pain",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["case_id"] == "CP-TEST-001"
        assert data["saved"]["case"] is True

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.create_pilot_case", new_callable=AsyncMock)
    @patch("api.routers.cardio_persistence_router.save_ai_extraction", new_callable=AsyncMock)
    def test_persist_case_with_extraction(self, mock_ext, mock_create, mock_pool):
        mock_create.return_value = MOCK_CASE
        mock_ext.return_value = MOCK_EXTRACTION
        resp = client.post("/v1/cardio/pilot/cases", json={
            "case_id": "CP-TEST-002",
            "raw_narrative": "test",
            "ai_extraction": {
                "extraction_id": "EXT-001",
                "model": "gpt-4o-mini",
                "extraction_source": "ai",
                "confidence": 0.9,
                "fields_json": {"age": 64},
            },
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["saved"]["ai_extraction"] is True

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.create_pilot_case", new_callable=AsyncMock)
    def test_persist_case_duplicate_conflict(self, mock_create, mock_pool):
        from repositories.errors import DatabaseWriteError
        mock_create.side_effect = DatabaseWriteError("pilot_cases", "duplicate key value violates unique constraint")
        resp = client.post("/v1/cardio/pilot/cases", json={
            "case_id": "CP-DUPLICATE",
            "raw_narrative": "test",
        })
        assert resp.status_code == 409

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.list_pilot_cases", new_callable=AsyncMock)
    def test_list_cases(self, mock_list, mock_pool):
        mock_list.return_value = [MOCK_CASE]
        resp = client.get("/v1/cardio/pilot/cases")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.get_case_bundle", new_callable=AsyncMock)
    def test_read_case_bundle(self, mock_bundle, mock_pool):
        mock_bundle.return_value = MOCK_BUNDLE
        resp = client.get("/v1/cardio/pilot/cases/CP-TEST-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["case"]["case_id"] == "CP-TEST-001"
        assert data["ai_extraction"]["extraction_id"] == "EXT-001"
        assert len(data["reviewer_feedback"]) == 1

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.get_case_bundle", new_callable=AsyncMock)
    def test_read_case_bundle_not_found(self, mock_bundle, mock_pool):
        mock_bundle.return_value = None
        resp = client.get("/v1/cardio/pilot/cases/NONEXISTENT")
        assert resp.status_code == 404


# ── Reviewer feedback endpoint tests ─────────────────────────────


class TestReviewerFeedbackEndpoint:

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.get_pilot_case", new_callable=AsyncMock)
    @patch("api.routers.cardio_persistence_router.save_reviewer_feedback", new_callable=AsyncMock)
    @patch("api.routers.cardio_persistence_router.update_case_status", new_callable=AsyncMock)
    def test_add_feedback(self, mock_update, mock_save, mock_get, mock_pool):
        mock_get.return_value = MOCK_CASE
        mock_save.return_value = MOCK_FEEDBACK
        mock_update.return_value = {**MOCK_CASE, "current_status": "reviewed"}

        resp = client.post("/v1/cardio/pilot/cases/CP-TEST-001/review", json={
            "route_appropriate": "agree",
            "usefulness_score": 4,
            "reviewer_name": "Dr. Test",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["feedback"]["route_appropriate"] == "agree"
        assert data["case_status_updated"] is True

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.get_pilot_case", new_callable=AsyncMock)
    def test_add_feedback_case_not_found(self, mock_get, mock_pool):
        mock_get.return_value = None
        resp = client.post("/v1/cardio/pilot/cases/NONEXISTENT/review", json={
            "route_appropriate": "agree",
            "usefulness_score": 3,
        })
        assert resp.status_code == 404


# ── Session summary endpoint tests ───────────────────────────────


class TestSessionSummaryEndpoints:

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.save_session_summary", new_callable=AsyncMock)
    def test_save_summary(self, mock_save, mock_pool):
        mock_save.return_value = MOCK_SUMMARY
        resp = client.post(f"/v1/cardio/pilot/sessions/{MOCK_SESSION['id']}/summary", json={
            "summary_id": "SUM-001",
            "metrics_json": {"cases_processed": 5},
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["summary"]["summary_id"] == "SUM-001"

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.get_session_summary", new_callable=AsyncMock)
    def test_read_summary(self, mock_get, mock_pool):
        mock_get.return_value = MOCK_SUMMARY
        resp = client.get(f"/v1/cardio/pilot/sessions/{MOCK_SESSION['id']}/summary")
        assert resp.status_code == 200
        assert resp.json()["summary"]["summary_id"] == "SUM-001"

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_configured)
    @patch("api.routers.cardio_persistence_router.get_pool")
    @patch("api.routers.cardio_persistence_router.get_session_summary", new_callable=AsyncMock)
    def test_read_summary_not_found(self, mock_get, mock_pool):
        mock_get.return_value = None
        resp = client.get(f"/v1/cardio/pilot/sessions/{str(uuid4())}/summary")
        assert resp.status_code == 404


# ── Database not configured tests ────────────────────────────────


class TestDatabaseNotConfigured:

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_not_configured)
    def test_sessions_returns_503(self):
        resp = client.get("/v1/cardio/pilot/sessions")
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"].lower()

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_not_configured)
    def test_cases_returns_503(self):
        resp = client.get("/v1/cardio/pilot/cases")
        assert resp.status_code == 503

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_not_configured)
    def test_case_bundle_returns_503(self):
        resp = client.get("/v1/cardio/pilot/cases/ANY")
        assert resp.status_code == 503

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_not_configured)
    def test_create_session_returns_503(self):
        resp = client.post("/v1/cardio/pilot/sessions", json={"label": "test"})
        assert resp.status_code == 503

    @patch("api.routers.cardio_persistence_router.database_url_configured", _db_not_configured)
    def test_persist_case_returns_503(self):
        resp = client.post("/v1/cardio/pilot/cases", json={"case_id": "X", "raw_narrative": "x"})
        assert resp.status_code == 503


# ── Existing endpoint isolation tests ────────────────────────────


class TestExistingEndpointsUnaffected:

    def test_healthz_still_works(self):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_root_still_works(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Soficca" in resp.json()["service"]

    def test_contract_still_works(self):
        resp = client.get("/contract")
        assert resp.status_code == 200

    def test_cardio_contract_still_works(self):
        resp = client.get("/v1/cardio/contract")
        assert resp.status_code == 200
