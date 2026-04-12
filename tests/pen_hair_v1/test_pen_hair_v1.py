import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from api.main import app
from pen_hair_v1.examples import canonical_hypertension_response_example
from pen_hair_v1.request_adapter import map_frontend_intake_to_request
from pen_hair_v1.schema import PenIntakeRequest
from pen_hair_v1.service import evaluate_pen_intake


def _valid_payload() -> dict:
    return {
        "age": 34,
        "norwood_stage": 3,
        "loss_noticed": "Last 12 months",
        "loss_areas": ["temples", "crown"],
        "main_goal": "regrowth",
        "high_blood_pressure": True,
        "cardiovascular_conditions": ["hypertension"],
        "current_medication": True,
        "medication_detail": "amlodipine",
        "prior_treatment_use": False,
        "which_treatment": [],
        "had_side_effects": False,
        "side_effect_detail": None,
        "scalp_sensitivities": False,
        "scalp_detail": None,
        "treatment_preference": "balanced",
        "routine_consistency": "high",
        "priority_factor": "safety",
        "baseline_photos_uploaded": True,
    }


def test_request_validation_rejects_underage() -> None:
    payload = _valid_payload()
    payload["age"] = 16

    with pytest.raises(ValidationError):
        PenIntakeRequest.model_validate(payload)


def test_hypertension_excludes_oral_and_selects_topical_path() -> None:
    request = PenIntakeRequest.model_validate(_valid_payload())
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "topical_treatment"
    assert [option.value for option in response.decision.excluded_options] == ["oral_treatment"]
    assert "HIGH_BLOOD_PRESSURE" in response.decision.flags


def test_response_contract_shape() -> None:
    request = PenIntakeRequest.model_validate(_valid_payload())
    response = evaluate_pen_intake(request).model_dump(mode="python")

    assert set(response.keys()) == {"versions", "decision", "trace", "journey_views", "frontend_adapter"}
    assert set(response["decision"].keys()) == {
        "status",
        "decision_path",
        "title",
        "explanation",
        "flags",
        "excluded_options",
    }

    assert set(response["frontend_adapter"].keys()) == {"evaluation", "journey"}


def test_journey_views_include_all_expected_states() -> None:
    request = PenIntakeRequest.model_validate(_valid_payload())
    response = evaluate_pen_intake(request)

    assert set(response.journey_views.model_dump(mode="python").keys()) == {
        "month_0",
        "week_6",
        "month_3",
        "month_6",
    }
    assert set(response.frontend_adapter.journey.model_dump(mode="python").keys()) == {
        "month_0",
        "week_6",
        "month_3",
        "month_6",
    }


def test_frontend_adapter_mirrors_canonical_sections() -> None:
    request = PenIntakeRequest.model_validate(_valid_payload())
    response = evaluate_pen_intake(request)

    assert response.frontend_adapter.evaluation.decision_path == response.decision.decision_path
    assert response.frontend_adapter.evaluation.trace_evidence == response.trace.trace_evidence
    assert response.frontend_adapter.journey.model_dump(mode="python") == response.journey_views.model_dump(mode="python")


def test_frontend_intake_mapper_supports_camel_case() -> None:
    mapped = map_frontend_intake_to_request(
        {
            "age": 34,
            "norwoodStage": 3,
            "lossNoticed": "last 12 months",
            "lossAreas": ["temples", "crown"],
            "mainGoal": "regrowth",
            "highBloodPressure": True,
            "cardiovascularConditions": ["hypertension"],
            "currentMedication": True,
            "medicationDetail": "amlodipine",
            "priorTreatmentUse": False,
            "whichTreatment": [],
            "hadSideEffects": False,
            "sideEffectDetail": None,
            "scalpSensitivities": False,
            "scalpDetail": None,
            "treatmentPreference": "balanced",
            "routineConsistency": "high",
            "priorityFactor": "safety",
            "baselinePhotosUploaded": True,
        }
    )

    assert mapped.norwood_stage == 3
    assert mapped.high_blood_pressure is True


def test_pen_evaluate_endpoint_returns_frontend_adapter() -> None:
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/v1/pen/evaluate", json=_valid_payload())
    assert response.status_code == 200
    data = response.json()

    assert "frontend_adapter" in data
    assert data["frontend_adapter"]["evaluation"]["decision_path"] == "topical_treatment"
    assert set(data["frontend_adapter"]["journey"].keys()) == {"month_0", "week_6", "month_3", "month_6"}


def test_canonical_example_includes_frontend_adapter() -> None:
    data = canonical_hypertension_response_example()
    assert data["decision"]["decision_path"] == "topical_treatment"
    assert data["decision"]["excluded_options"] == ["oral_treatment"]
    assert "frontend_adapter" in data
    assert data["frontend_adapter"]["evaluation"]["decision_path"] == "topical_treatment"


def test_pen_router_endpoints_available_from_main() -> None:
    repo_root = str(Path(".").resolve())
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    spec = importlib.util.spec_from_file_location("api_main", Path("api/main.py"))
    assert spec and spec.loader
    api_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_main)

    route_paths = {route.path for route in api_main.app.routes}
    assert "/v1/pen/evaluate" in route_paths
    assert "/v1/pen/contract" in route_paths
