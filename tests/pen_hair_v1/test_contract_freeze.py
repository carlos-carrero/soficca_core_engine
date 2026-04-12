from __future__ import annotations

from pen_hair_v1.contract_freeze import (
    STABLE_JOURNEY_STATES,
    STABLE_TOP_LEVEL_KEYS,
    validate_frozen_pen_contract_shape,
)
from pen_hair_v1.schema import PenIntakeRequest
from pen_hair_v1.service import evaluate_pen_intake
from tests.pen_hair_v1.golden_cases import get_pen_golden_cases


def test_frozen_contract_shape_for_all_pen_golden_cases() -> None:
    for case in get_pen_golden_cases():
        payload = PenIntakeRequest.model_validate(case["payload"])
        response = evaluate_pen_intake(payload).model_dump(mode="python")
        issues = validate_frozen_pen_contract_shape(response)
        assert issues == [], f"{case['name']} failed contract freeze: {issues}"


def test_canonical_hypertension_case_frozen_behavior() -> None:
    case = next(item for item in get_pen_golden_cases() if item["name"] == "canonical_hypertension_case")
    payload = PenIntakeRequest.model_validate(case["payload"])
    response = evaluate_pen_intake(payload).model_dump(mode="python")

    assert response["decision"]["decision_path"] == "topical_treatment"
    assert response["decision"]["status"] == "DECIDED"
    assert response["decision"]["excluded_options"] == ["oral_treatment"]
    assert "HIGH_BLOOD_PRESSURE" in response["decision"]["flags"]
    assert response["decision_rationale"]["safety_summary"] is not None
    assert set(response["journey_views"].keys()) == STABLE_JOURNEY_STATES
    assert set(response["frontend_adapter"]["journey"].keys()) == STABLE_JOURNEY_STATES
    assert set(response.keys()) == STABLE_TOP_LEVEL_KEYS
