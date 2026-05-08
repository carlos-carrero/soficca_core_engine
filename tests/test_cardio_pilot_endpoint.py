"""
Tests for POST /v1/cardio/pilot/report

Verifies the pilot adapter maps extraction → engine input → real CardioReport.
Does NOT test engine logic (that's in tests/cardio_v1/).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _post(extraction: dict, case_id: str = "TEST-001", raw_text: str = "test") -> dict:
    body = {
        "case_id": case_id,
        "raw_text": raw_text,
        "source": "test",
        "extraction": extraction,
    }
    resp = client.post("/v1/cardio/pilot/report", json=body)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    return resp.json()


class TestPilotEndpointEmergency:
    """Emergency red-flag case: syncope + chest pain → ESCALATED."""

    def test_emergency_route(self):
        data = _post({
            "age": 64,
            "chest_pain_present": True,
            "pain_duration_minutes": 10,
            "pain_character": "pressure",
            "pain_severity": "high",
            "pain_radiation": "left_arm",
            "dyspnea": False,
            "syncope": True,
            "systolic_bp": 120,
            "heart_rate": 96,
            "known_cad": False,
            "current_meds_none": True,
        })
        assert data["case_id"] == "TEST-001"
        assert data["human_review_required"] is True
        assert data["pilot_mode"] == "deterministic_routing_v1"
        report = data["engine_report"]
        assert report["decision"]["status"] == "ESCALATED"
        assert report["decision"]["path"] == "PATH_EMERGENCY_NOW"
        assert report["decision"]["urgency_level"] == "EMERGENCY"
        assert report["safety"]["status"] == "TRIGGERED"


class TestPilotEndpointNeedsMoreInfo:
    """Incomplete extraction → NEEDS_MORE_INFO."""

    def test_missing_fields(self):
        data = _post({
            "age": 62,
            "chest_pain_present": True,
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 124,
            "heart_rate": 80,
            "current_meds_none": True,
        })
        report = data["engine_report"]
        assert report["decision"]["status"] == "NEEDS_MORE_INFO"
        assert report["decision"]["path"] is None
        assert len(report["decision"]["missing_fields"]) > 0


class TestPilotEndpointConflict:
    """Contradictory extraction → CONFLICT."""

    def test_conflict_case(self):
        data = _post({
            "age": 59,
            "chest_pain_present": False,
            "pain_duration_minutes": 20,
            "pain_character": "crushing",
            "pain_severity": "high",
            "pain_radiation": "jaw",
            "exertional_chest_pain": True,
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 122,
            "heart_rate": 84,
            "known_cad": False,
            "current_meds_none": True,
        })
        report = data["engine_report"]
        assert report["decision"]["status"] == "CONFLICT"
        assert report["decision"]["path"] is None
        assert len(report["trace"]["conflicts_detected"]) > 0


class TestPilotEndpointRoutine:
    """Stable complete case → DECIDED / PATH_ROUTINE."""

    def test_routine_review(self):
        data = _post({
            "age": 60,
            "chest_pain_present": True,
            "pain_duration_minutes": 15,
            "pain_character": "pressure",
            "pain_severity": "low",
            "pain_radiation": "none",
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 122,
            "heart_rate": 78,
            "known_cad": False,
            "current_meds_none": True,
            "exertional_chest_pain": False,
            "diaphoresis": False,
            "cv_risk_factors_count": 1,
        })
        report = data["engine_report"]
        assert report["decision"]["status"] == "DECIDED"
        assert report["decision"]["path"] == "PATH_ROUTINE"
        assert report["decision"]["urgency_level"] == "ROUTINE"


class TestPilotEndpointUrgent:
    """Urgent escalation case → DECIDED / PATH_URGENT_SAME_DAY."""

    def test_urgent_escalation(self):
        data = _post({
            "age": 63,
            "chest_pain_present": True,
            "pain_duration_minutes": 20,
            "pain_character": "pressure",
            "pain_severity": "moderate",
            "pain_radiation": "jaw",
            "exertional_chest_pain": True,
            "dyspnea": False,
            "syncope": False,
            "systolic_bp": 126,
            "heart_rate": 88,
            "known_cad": False,
            "current_meds_none": True,
            "diaphoresis": False,
            "cv_risk_factors_count": 1,
        })
        report = data["engine_report"]
        assert report["decision"]["status"] == "DECIDED"
        assert report["decision"]["path"] == "PATH_URGENT_SAME_DAY"
        assert report["decision"]["urgency_level"] == "URGENT"


class TestPilotEndpointValidation:
    """Endpoint rejects unexpected fields."""

    def test_extra_field_rejected(self):
        body = {
            "case_id": "TEST-V1",
            "raw_text": "test",
            "source": "test",
            "extraction": {
                "age": 60,
                "diagnosis": "MI",  # forbidden field
            },
        }
        resp = client.post("/v1/cardio/pilot/report", json=body)
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"


class TestPilotEndpointResponseShape:
    """Verify response wrapper shape."""

    def test_response_contains_all_fields(self):
        data = _post({"age": 60, "chest_pain_present": True, "current_meds_none": True})
        assert "case_id" in data
        assert "source" in data
        assert "raw_text" in data
        assert "engine_input" in data
        assert "engine_report" in data
        assert "human_review_required" in data
        assert "pilot_mode" in data
        assert "state" in data["engine_input"]
        assert "context" in data["engine_input"]
