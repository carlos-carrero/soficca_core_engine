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
from tests.pen_hair_v1.golden_cases import get_pen_golden_cases


def _valid_payload() -> dict:
    return {
        "age": 34,
        "norwood_stage": 3,
        "loss_noticed": "Last 12 months",
        "loss_areas": ["temples", "crown"],
        "main_goal": "regrowth",
        "high_blood_pressure": True,
        "cardiovascular_conditions": False,
        "current_medication": True,
        "medication_detail": "amlodipine",
        "prior_treatment_use": False,
        "which_treatment": "",
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


def test_frontend_style_boolean_and_string_fields_validate() -> None:
    payload = _valid_payload()
    payload["cardiovascular_conditions"] = False
    payload["which_treatment"] = ""

    validated = PenIntakeRequest.model_validate(payload)
    assert validated.cardiovascular_conditions is False
    assert validated.which_treatment is None


def test_legacy_list_style_fields_are_backwards_coerced() -> None:
    payload = _valid_payload()
    payload["cardiovascular_conditions"] = ["hypertension"]
    payload["which_treatment"] = ["topical", "oral"]

    validated = PenIntakeRequest.model_validate(payload)
    assert validated.cardiovascular_conditions is True
    assert validated.which_treatment == "topical"


def test_hypertension_excludes_oral_and_selects_topical_path() -> None:
    request = PenIntakeRequest.model_validate(_valid_payload())
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "topical_treatment"
    assert [option.value for option in response.decision.excluded_options] == ["oral_treatment"]
    assert "HIGH_BLOOD_PRESSURE" in response.decision.flags
    assert "high blood pressure" in response.decision.explanation.lower()
    assert "RULE_EXCLUDE_ORAL_FOR_HYPERTENSION_V1" in response.trace.rules_triggered


def test_cardiovascular_conditions_route_to_manual_review() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = True
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "manual_review"
    assert "CARDIOVASCULAR_CONDITION" in response.decision.flags
    assert [option.value for option in response.decision.excluded_options] == ["oral_treatment"]


def test_prior_treatment_side_effects_route_to_manual_review() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["prior_treatment_use"] = True
    payload["had_side_effects"] = True
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "manual_review"
    assert "PRIOR_SIDE_EFFECTS" in response.decision.flags


def test_unknown_critical_inputs_route_to_needs_more_information() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["treatment_preference"] = "unknown"
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.status.value == "NEEDS_MORE_INFO"
    assert response.decision.decision_path.value == "needs_more_information"


def test_manual_review_precedes_missing_info_for_cardiovascular_risk() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = True
    payload["treatment_preference"] = "unknown"
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "manual_review"
    assert "CARDIOVASCULAR_CONDITION" in response.decision.flags


def test_manual_review_precedes_missing_info_for_prior_side_effects() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["prior_treatment_use"] = True
    payload["had_side_effects"] = True
    payload["priority_factor"] = "unknown"
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "manual_review"
    assert "PRIOR_SIDE_EFFECTS" in response.decision.flags


def test_blank_critical_inputs_are_treated_as_needs_more_information() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["routine_consistency"] = "   "
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "needs_more_information"


def test_support_path_branch_for_scalp_sensitivity() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["scalp_sensitivities"] = True
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "topical_treatment_with_support"
    assert "SCALP_SENSITIVITY" in response.decision.flags


def test_not_sure_variant_routes_to_needs_more_information() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["priority_factor"] = "not sure"
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "needs_more_information"


def test_simpler_routine_preference_routes_to_support_path() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["treatment_preference"] = "simpler_routine"
    payload["routine_consistency"] = "high"
    payload["priority_factor"] = "efficacy"
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "topical_treatment_with_support"
    assert "RULE_SUPPORT_PATH_SIMPLER_ROUTINE_PREFERENCE_V1" in response.trace.rules_triggered


def test_convenience_priority_routes_to_support_path() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["priority_factor"] = "convenience"
    payload["routine_consistency"] = "high"
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "topical_treatment_with_support"
    assert "RULE_SUPPORT_PATH_COMFORT_PRIORITY_V1" in response.trace.rules_triggered


@pytest.mark.parametrize(
    ("name", "mutations", "expected_decision_path"),
    [
        ("canonical_hypertension", {}, "topical_treatment"),
        (
            "no_hbp_no_cardio_topical_high_consistency",
            {
                "high_blood_pressure": False,
                "cardiovascular_conditions": False,
                "treatment_preference": "topical",
                "routine_consistency": "high",
                "priority_factor": "efficacy",
            },
            "topical_treatment",
        ),
        (
            "no_hbp_oral_preference_high_consistency",
            {
                "high_blood_pressure": False,
                "cardiovascular_conditions": False,
                "treatment_preference": "oral",
                "routine_consistency": "high",
                "priority_factor": "efficacy",
            },
            "oral_treatment",
        ),
        (
            "cardiovascular_conditions_true",
            {"high_blood_pressure": False, "cardiovascular_conditions": True},
            "manual_review",
        ),
        (
            "prior_treatment_side_effects",
            {
                "high_blood_pressure": False,
                "cardiovascular_conditions": False,
                "prior_treatment_use": True,
                "had_side_effects": True,
            },
            "manual_review",
        ),
        (
            "scalp_sensitivity",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "scalp_sensitivities": True},
            "topical_treatment_with_support",
        ),
        (
            "low_consistency_support",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "routine_consistency": "low"},
            "topical_treatment_with_support",
        ),
        (
            "comfort_priority_support",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "priority_factor": "comfort"},
            "topical_treatment_with_support",
        ),
        (
            "convenience_priority_support",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "priority_factor": "convenience"},
            "topical_treatment_with_support",
        ),
        (
            "simpler_routine_preference_support",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "treatment_preference": "simpler_routine"},
            "topical_treatment_with_support",
        ),
        (
            "missing_critical_input",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "treatment_preference": "unknown"},
            "needs_more_information",
        ),
    ],
)
def test_pen_decision_matrix_regression(name: str, mutations: dict, expected_decision_path: str) -> None:
    payload = _valid_payload()
    payload.update(mutations)
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == expected_decision_path
    assert response.frontend_adapter.evaluation.decision_path.value == expected_decision_path
    assert response.trace.rules_triggered


def test_oral_preference_routes_to_oral_without_blockers() -> None:
    payload = _valid_payload()
    payload["high_blood_pressure"] = False
    payload["cardiovascular_conditions"] = False
    payload["treatment_preference"] = "oral"
    payload["routine_consistency"] = "high"
    payload["priority_factor"] = "efficacy"
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == "oral_treatment"
    assert "oral" in response.decision.title.lower()
    assert "oral" in response.decision.explanation.lower()
    assert "oral treatment selected" in response.decision_rationale.primary_reason.lower()
    assert "RULE_ORAL_TREATMENT_PREFERENCE_SELECTED_V1" in response.trace.rules_triggered


def test_response_contract_shape() -> None:
    request = PenIntakeRequest.model_validate(_valid_payload())
    response = evaluate_pen_intake(request).model_dump(mode="python")

    assert set(response.keys()) == {
        "versions",
        "decision",
        "decision_rationale",
        "trace",
        "journey_views",
        "frontend_adapter",
    }
    assert set(response["decision"].keys()) == {
        "status",
        "decision_path",
        "title",
        "explanation",
        "flags",
        "excluded_options",
    }

    assert set(response["frontend_adapter"].keys()) == {"evaluation", "journey"}
    assert set(response["decision_rationale"].keys()) == {
        "primary_reason",
        "supporting_reasons",
        "safety_summary",
        "why_not_selected",
    }


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


@pytest.mark.parametrize(
    ("name", "mutations", "expected_decision_path"),
    [
        ("topical_hypertension", {"high_blood_pressure": True, "cardiovascular_conditions": False}, "topical_treatment"),
        ("support_low_consistency", {"high_blood_pressure": False, "cardiovascular_conditions": False, "routine_consistency": "low"}, "topical_treatment_with_support"),
        ("manual_cardio", {"high_blood_pressure": False, "cardiovascular_conditions": True}, "manual_review"),
        ("needs_info_unknown", {"high_blood_pressure": False, "cardiovascular_conditions": False, "treatment_preference": "unknown"}, "needs_more_information"),
    ],
)
def test_journey_stage_text_is_temporally_distinct(name: str, mutations: dict, expected_decision_path: str) -> None:
    payload = _valid_payload()
    payload.update(mutations)
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    assert response.decision.decision_path.value == expected_decision_path
    recommendations = [
        response.journey_views.month_0.recommendation.body,
        response.journey_views.week_6.recommendation.body,
        response.journey_views.month_3.recommendation.body,
        response.journey_views.month_6.recommendation.body,
    ]
    narratives = [
        response.journey_views.month_0.narrative.body,
        response.journey_views.week_6.narrative.body,
        response.journey_views.month_3.narrative.body,
        response.journey_views.month_6.narrative.body,
    ]
    assert len(set(recommendations)) == 4
    assert len(set(narratives)) == 4


@pytest.mark.parametrize(
    ("name", "mutations", "expected_badge_contains"),
    [
        (
            "topical_hypertension",
            {"high_blood_pressure": True, "cardiovascular_conditions": False, "treatment_preference": "balanced"},
            "blood-pressure oral-exclusion safety signal",
        ),
        (
            "oral_treatment_selected",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "treatment_preference": "oral"},
            "oral treatment preference signal",
        ),
        (
            "support_low_consistency",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "routine_consistency": "low"},
            "routine-consistency support signal",
        ),
        (
            "support_scalp",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "scalp_sensitivities": True},
            "scalp-sensitivity support signal",
        ),
        (
            "manual_cardio",
            {"high_blood_pressure": False, "cardiovascular_conditions": True},
            "cardiovascular risk signal",
        ),
        (
            "manual_prior_side_effects",
            {
                "high_blood_pressure": False,
                "cardiovascular_conditions": False,
                "prior_treatment_use": True,
                "had_side_effects": True,
            },
            "prior treatment side-effect signal",
        ),
        (
            "needs_info_unknown",
            {"high_blood_pressure": False, "cardiovascular_conditions": False, "treatment_preference": "unknown"},
            "missing critical preference/consistency inputs",
        ),
    ],
)
def test_journey_stage_badge_carries_stage_trace_driver(name: str, mutations: dict, expected_badge_contains: str) -> None:
    payload = _valid_payload()
    payload.update(mutations)
    request = PenIntakeRequest.model_validate(payload)
    response = evaluate_pen_intake(request)

    month_0_badge = response.journey_views.month_0.decision_trace_badge
    week_6_badge = response.journey_views.week_6.decision_trace_badge
    month_3_badge = response.journey_views.month_3.decision_trace_badge
    month_6_badge = response.journey_views.month_6.decision_trace_badge

    assert expected_badge_contains in month_0_badge
    assert "month_0 trace:" in month_0_badge
    assert "week_6 trace:" in week_6_badge
    assert "month_3 trace:" in month_3_badge
    assert "month_6 trace:" in month_6_badge


def test_frontend_adapter_mirrors_canonical_sections() -> None:
    request = PenIntakeRequest.model_validate(_valid_payload())
    response = evaluate_pen_intake(request)

    assert response.frontend_adapter.evaluation.decision_path == response.decision.decision_path
    assert response.frontend_adapter.evaluation.trace_evidence == response.trace.trace_evidence
    journey_dump = response.frontend_adapter.journey.model_dump(mode="python")
    assert set(journey_dump.keys()) == {"month_0", "week_6", "month_3", "month_6"}
    assert "hero" in journey_dump["month_0"]
    assert "items" in journey_dump["month_0"]["progress_strip"]
    assert "steps" in journey_dump["month_0"]["progress_photos"]
    assert set(response.model_dump(mode="python").keys()) == {
        "versions",
        "decision",
        "decision_rationale",
        "trace",
        "journey_views",
        "frontend_adapter",
    }


def test_frontend_intake_mapper_supports_camel_case() -> None:
    mapped = map_frontend_intake_to_request(
        {
            "age": 34,
            "norwoodStage": 3,
            "lossNoticed": "last 12 months",
            "lossAreas": ["temples", "crown"],
            "mainGoal": "regrowth",
            "highBloodPressure": True,
            "cardiovascularConditions": False,
            "currentMedication": True,
            "medicationDetail": "amlodipine",
            "priorTreatmentUse": False,
            "whichTreatment": "",
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
    assert "decision_rationale" in data
    assert "frontend_adapter" in data
    assert data["frontend_adapter"]["evaluation"]["decision_path"] == "topical_treatment"


@pytest.mark.parametrize("case", get_pen_golden_cases(), ids=lambda case: case["name"])
def test_pen_golden_cases(case: dict) -> None:
    request = PenIntakeRequest.model_validate(case["payload"])
    response = evaluate_pen_intake(request).model_dump(mode="python")

    assert response["decision"]["decision_path"] == case["decision_path"]
    assert response["decision"]["status"] == case["status"]
    for flag in case["expected_flags"]:
        assert flag in response["decision"]["flags"]
    assert response["decision"]["excluded_options"] == case["expected_excluded_options"]
    assert case["rationale_primary_contains"] in response["decision_rationale"]["primary_reason"].lower()
    safety_summary = response["decision_rationale"]["safety_summary"]
    if case["rationale_safety_contains"] is None:
        assert safety_summary is None
    else:
        assert safety_summary is not None
        assert case["rationale_safety_contains"] in safety_summary.lower()
    assert set(response["journey_views"].keys()) == {"month_0", "week_6", "month_3", "month_6"}
    assert set(response["frontend_adapter"]["journey"].keys()) == {"month_0", "week_6", "month_3", "month_6"}
    assert set(response.keys()) == {
        "versions",
        "decision",
        "decision_rationale",
        "trace",
        "journey_views",
        "frontend_adapter",
    }


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
