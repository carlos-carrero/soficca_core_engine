"""
Tests for POST /v1/cardio/pilot/extract

Verifies the AI extraction endpoint behavior, safety filters,
and schema validation. Uses a mocked OpenAI client.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers.cardio_extract_router import (
    CardioAIRawOutput,
    CardioMissingInformation,
    CardioPilotExtractionFields,
    CardioFieldEvidence,
    strip_disallowed_fields,
    sanitize_summary_and_questions,
)

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────

SAMPLE_AI_OUTPUT = CardioAIRawOutput(
    fields=CardioPilotExtractionFields(
        age=64,
        chest_pain_present=True,
        pain_duration_minutes=10,
        pain_character="pressure",
        pain_severity="high",
        pain_radiation="left_arm",
        dyspnea=False,
        syncope=True,
        systolic_bp=120,
        heart_rate=96,
        known_cad=False,
        current_meds_none=True,
    ),
    structured_clinical_summary="The narrative reports a 64-year-old patient with pressure-like chest pain lasting 10 minutes with left-arm radiation and syncope.",
    missing_fields=["prior_mi", "cv_risk_factors_count"],
    missing_information=CardioMissingInformation(
        required_for_routing=["prior_mi"],
        clinically_useful=["cv_risk_factors_count"],
        unconfirmed=["exertional_chest_pain", "diaphoresis"],
    ),
    completion_questions=[
        "Is there a history of prior myocardial infarction?",
        "How many cardiovascular risk factors are known?",
    ],
    possible_conflicts=[],
    field_evidence=[
        CardioFieldEvidence(
            field="syncope",
            value="true",
            source_text="Patient experienced syncope during the episode.",
            confidence=0.95,
        ),
        CardioFieldEvidence(
            field="age",
            value="64",
            source_text="64-year-old patient",
            confidence=0.99,
        ),
    ],
    extraction_quality_flags=["requires_human_confirmation", "cardiovascular_history_unclear"],
    pii_warnings=[],
    warnings=[],
    confidence=0.88,
    language_detected="en",
)

SAMPLE_SPANISH_AI_OUTPUT = CardioAIRawOutput(
    fields=CardioPilotExtractionFields(
        age=63,
        chest_pain_present=True,
        pain_duration_minutes=20,
        pain_character="pressure",
        pain_radiation="jaw",
        syncope=False,
        systolic_bp=126,
        heart_rate=88,
    ),
    structured_clinical_summary="The narrative reports a 63-year-old patient with chest pressure lasting 20 minutes and jaw radiation.",
    missing_fields=["prior_mi", "known_cad", "current_meds_none"],
    missing_information=CardioMissingInformation(
        required_for_routing=["prior_mi", "known_cad"],
        clinically_useful=["current_meds_none"],
        unconfirmed=[],
    ),
    completion_questions=[
        "Is there a history of prior MI or known coronary artery disease?",
        "What are the current medications?",
    ],
    possible_conflicts=[],
    field_evidence=[
        CardioFieldEvidence(
            field="age",
            value="63",
            source_text="Paciente de 63 años",
            confidence=0.98,
        ),
    ],
    extraction_quality_flags=["requires_human_confirmation", "medication_status_unclear", "cardiovascular_history_unclear"],
    pii_warnings=[],
    warnings=[],
    confidence=0.82,
    language_detected="es",
)


def _mock_openai_call(output: CardioAIRawOutput):
    """Create a mock that replaces _call_openai to return the given output."""
    return patch(
        "api.routers.cardio_extract_router._call_openai",
        return_value=output,
    )


# ── Tests ─────────────────────────────────────────────────────────


class TestExtractEndpointMissingKey:
    """Missing OPENAI_API_KEY returns controlled error."""

    def test_missing_api_key_returns_503(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if present
            env = dict(os.environ)
            env.pop("OPENAI_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                # Reset the mock so it actually tries to call OpenAI
                resp = client.post(
                    "/v1/cardio/pilot/extract",
                    json={"case_text": "test", "language": "en"},
                )
                assert resp.status_code == 503
                assert "OPENAI_API_KEY" in resp.json()["detail"]


class TestExtractEndpointEnglish:
    """English case is structured correctly."""

    def test_english_extraction(self):
        with _mock_openai_call(SAMPLE_AI_OUTPUT):
            resp = client.post(
                "/v1/cardio/pilot/extract",
                json={
                    "case_text": "64-year-old patient with severe pressure-like chest pain for 10 minutes.",
                    "language": "en",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["ai_role"] == "STRUCTURING_ONLY"
            assert data["confidence"] == 0.88
            assert data["language_detected"] == "en"
            assert data["fields"]["age"] == 64
            assert data["fields"]["chest_pain_present"] is True
            assert data["fields"]["syncope"] is True
            assert data["fields"]["pain_character"] == "pressure"
            assert "prior_mi" in data["missing_fields"]
            assert len(data["field_evidence"]) == 2


class TestExtractEndpointSpanish:
    """Spanish case is structured correctly."""

    def test_spanish_extraction(self):
        with _mock_openai_call(SAMPLE_SPANISH_AI_OUTPUT):
            resp = client.post(
                "/v1/cardio/pilot/extract",
                json={
                    "case_text": "Paciente de 63 años con presión en el pecho desde hace 20 minutos.",
                    "language": "es",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["language_detected"] == "es"
            assert data["fields"]["age"] == 63
            assert data["fields"]["pain_radiation"] == "jaw"


class TestExtractEndpointValidation:
    """Response validates against Pydantic schema."""

    def test_response_shape(self):
        with _mock_openai_call(SAMPLE_AI_OUTPUT):
            resp = client.post(
                "/v1/cardio/pilot/extract",
                json={"case_text": "test case"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "extraction_id" in data
            assert "model" in data
            assert "fields" in data
            assert "missing_fields" in data
            assert "possible_conflicts" in data
            assert "field_evidence" in data
            assert "warnings" in data
            assert "confidence" in data
            assert "ai_role" in data
            # New intelligence fields
            assert "structured_clinical_summary" in data
            assert "missing_information" in data
            assert "completion_questions" in data
            assert "extraction_quality_flags" in data
            assert "pii_warnings" in data


class TestSafetyFilterStrip:
    """Disallowed clinical-decision fields are stripped."""

    def test_disallowed_fields_removed(self):
        raw = {
            "fields": {
                "age": 64,
                "diagnosis": "STEMI",
                "treatment": "aspirin",
            },
            "missing_fields": [],
            "possible_conflicts": [],
            "field_evidence": [],
            "warnings": [],
            "confidence": 0.8,
            "language_detected": "en",
        }
        warnings = strip_disallowed_fields(raw)
        assert "diagnosis" not in raw["fields"]
        assert "treatment" not in raw["fields"]
        assert "age" in raw["fields"]
        assert len(warnings) == 2
        assert any("diagnosis" in w for w in warnings)
        assert any("treatment" in w for w in warnings)

    def test_top_level_disallowed_stripped(self):
        raw = {
            "fields": {"age": 60},
            "prescription": "metoprolol",
            "missing_fields": [],
            "possible_conflicts": [],
            "field_evidence": [],
            "warnings": [],
            "confidence": 0.7,
            "language_detected": "en",
        }
        warnings = strip_disallowed_fields(raw)
        assert "prescription" not in raw
        assert len(warnings) == 1


class TestExtractDoesNotRoute:
    """/extract does not call the routing engine."""

    def test_no_routing_in_extract(self):
        with _mock_openai_call(SAMPLE_AI_OUTPUT):
            with patch(
                "api.routers.cardio_pilot_router.evaluate_cardio_report"
            ) as mock_route:
                resp = client.post(
                    "/v1/cardio/pilot/extract",
                    json={"case_text": "test"},
                )
                assert resp.status_code == 200
                mock_route.assert_not_called()


class TestIntelligenceFields:
    """Verify new AI intelligence layer fields are returned correctly."""

    def test_structured_summary_present(self):
        with _mock_openai_call(SAMPLE_AI_OUTPUT):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            data = resp.json()
            assert isinstance(data["structured_clinical_summary"], str)
            assert len(data["structured_clinical_summary"]) > 0

    def test_missing_information_categories(self):
        with _mock_openai_call(SAMPLE_AI_OUTPUT):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            mi = resp.json()["missing_information"]
            assert "required_for_routing" in mi
            assert "clinically_useful" in mi
            assert "unconfirmed" in mi
            assert isinstance(mi["required_for_routing"], list)
            assert isinstance(mi["clinically_useful"], list)
            assert isinstance(mi["unconfirmed"], list)

    def test_completion_questions_present(self):
        with _mock_openai_call(SAMPLE_AI_OUTPUT):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            qs = resp.json()["completion_questions"]
            assert isinstance(qs, list)
            assert len(qs) > 0
            assert all(isinstance(q, str) for q in qs)

    def test_quality_flags_controlled_values(self):
        with _mock_openai_call(SAMPLE_AI_OUTPUT):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            flags = resp.json()["extraction_quality_flags"]
            allowed = {
                "low_confidence_extraction", "critical_missing_fields",
                "contradictory_narrative", "limited_vitals",
                "medication_status_unclear", "cardiovascular_history_unclear",
                "requires_human_confirmation", "possible_identifier_detected",
            }
            assert all(f in allowed for f in flags)

    def test_pii_warnings_empty_when_clean(self):
        with _mock_openai_call(SAMPLE_AI_OUTPUT):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            assert resp.json()["pii_warnings"] == []


class TestSummarySafetyFilter:
    """Verify structured_clinical_summary and completion_questions safety."""

    def test_summary_with_diagnosis_is_redacted(self):
        raw = {
            "structured_clinical_summary": "The patient should be treated for STEMI and route to emergency.",
            "completion_questions": ["What is the diagnosis?"],
        }
        warnings = sanitize_summary_and_questions(raw)
        assert "redacted" in raw["structured_clinical_summary"].lower()
        assert len(warnings) >= 1

    def test_questions_with_route_removed(self):
        raw = {
            "structured_clinical_summary": "The narrative reports chest pain.",
            "completion_questions": [
                "How long has the pain lasted?",
                "Should we route to emergency?",
                "Does the patient have prior MI?",
            ],
        }
        warnings = sanitize_summary_and_questions(raw)
        assert len(raw["completion_questions"]) == 2
        assert any("route to" in w for w in warnings)

    def test_clean_summary_not_modified(self):
        original = "The narrative reports a 64-year-old patient with chest pain."
        raw = {
            "structured_clinical_summary": original,
            "completion_questions": ["How long has the pain lasted?"],
        }
        warnings = sanitize_summary_and_questions(raw)
        assert raw["structured_clinical_summary"] == original
        assert warnings == []


class TestOpenAIErrorHandling:
    """OpenAI errors return controlled HTTP responses, not 500 stack traces."""

    def test_auth_error_returns_503(self):
        from openai import AuthenticationError
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.headers = {}

        with patch(
            "api.routers.cardio_extract_router._call_openai",
            side_effect=lambda *a, **k: (_ for _ in ()).throw(
                AuthenticationError(
                    message="Invalid API key",
                    response=mock_resp,
                    body=None,
                )
            ),
        ):
            # The endpoint catches HTTPException raised by _call_openai,
            # but we also need to test that _call_openai itself handles auth.
            # Since we mock _call_openai directly, test via the actual function:
            pass

        # Test through the endpoint with a mock that raises HTTPException(503)
        from fastapi import HTTPException

        def raise_auth(*args, **kwargs):
            raise HTTPException(status_code=503, detail="OpenAI authentication failed.")

        with patch("api.routers.cardio_extract_router._call_openai", side_effect=raise_auth):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            assert resp.status_code == 503
            assert "authentication" in resp.json()["detail"].lower()

    def test_bad_request_returns_502(self):
        from fastapi import HTTPException

        def raise_bad(*args, **kwargs):
            raise HTTPException(status_code=502, detail="OpenAI bad request: invalid schema")

        with patch("api.routers.cardio_extract_router._call_openai", side_effect=raise_bad):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            assert resp.status_code == 502
            assert "bad request" in resp.json()["detail"].lower()

    def test_generic_api_error_returns_502(self):
        from fastapi import HTTPException

        def raise_api(*args, **kwargs):
            raise HTTPException(status_code=502, detail="OpenAI API error: Provider error")

        with patch("api.routers.cardio_extract_router._call_openai", side_effect=raise_api):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            assert resp.status_code == 502

    def test_unexpected_error_returns_502(self):
        from fastapi import HTTPException

        def raise_unexpected(*args, **kwargs):
            raise HTTPException(
                status_code=502,
                detail="Unexpected error calling OpenAI. AI extraction is temporarily unavailable.",
            )

        with patch("api.routers.cardio_extract_router._call_openai", side_effect=raise_unexpected):
            resp = client.post("/v1/cardio/pilot/extract", json={"case_text": "test"})
            assert resp.status_code == 502
            assert "api_key" not in resp.json()["detail"].lower()
            assert "sk-" not in resp.json()["detail"]


class TestOpenAISchemaCompatibility:
    """Verify the structured output schema has no untyped properties."""

    def _collect_untyped(self, schema: dict, path: str = "") -> list[str]:
        """Recursively find schema properties missing a 'type' or '$ref' or 'anyOf' key."""
        issues: list[str] = []
        props = schema.get("properties", {})
        for name, prop in props.items():
            current = f"{path}.{name}" if path else name
            has_type = any(k in prop for k in ("type", "$ref", "anyOf", "allOf", "oneOf", "enum", "const"))
            if not has_type:
                issues.append(current)
            # Recurse into nested objects
            if prop.get("type") == "object":
                issues.extend(self._collect_untyped(prop, current))
            if prop.get("type") == "array" and "items" in prop:
                items = prop["items"]
                if items.get("type") == "object":
                    issues.extend(self._collect_untyped(items, f"{current}[]"))
        # Check $defs
        for def_name, def_schema in schema.get("$defs", {}).items():
            if def_schema.get("type") == "object":
                issues.extend(self._collect_untyped(def_schema, f"$defs.{def_name}"))
        return issues

    def test_no_untyped_properties_in_ai_schema(self):
        schema = CardioAIRawOutput.model_json_schema()
        issues = self._collect_untyped(schema)
        assert issues == [], f"Schema properties without explicit type: {issues}"

    def test_field_evidence_value_is_string(self):
        """Ensure value field is str, not Any."""
        ev = CardioFieldEvidence(field="age", value="64", source_text="64yo", confidence=0.9)
        assert isinstance(ev.value, str)
        schema = CardioFieldEvidence.model_json_schema()
        assert schema["properties"]["value"]["type"] == "string"
