from __future__ import annotations

from typing import Any, Dict, List


def _base_payload() -> Dict[str, Any]:
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
        "treatment_preference": "topical",
        "routine_consistency": "high",
        "priority_factor": "safety",
        "baseline_photos_uploaded": True,
    }


def get_pen_golden_cases() -> List[Dict[str, Any]]:
    base = _base_payload()

    cardiovascular_case = {**base, "high_blood_pressure": False, "cardiovascular_conditions": True}
    side_effect_case = {
        **base,
        "high_blood_pressure": False,
        "cardiovascular_conditions": False,
        "prior_treatment_use": True,
        "had_side_effects": True,
    }
    missing_info_case = {
        **base,
        "high_blood_pressure": False,
        "cardiovascular_conditions": False,
        "treatment_preference": "unknown",
    }
    support_case = {
        **base,
        "high_blood_pressure": False,
        "cardiovascular_conditions": False,
        "scalp_sensitivities": True,
        "routine_consistency": "low",
    }
    convenience_support_case = {
        **base,
        "high_blood_pressure": False,
        "cardiovascular_conditions": False,
        "priority_factor": "convenience",
        "routine_consistency": "high",
    }
    simpler_routine_preference_case = {
        **base,
        "high_blood_pressure": False,
        "cardiovascular_conditions": False,
        "treatment_preference": "simpler_routine",
        "routine_consistency": "high",
        "priority_factor": "efficacy",
    }
    oral_preference_topical_case = {
        **base,
        "high_blood_pressure": False,
        "cardiovascular_conditions": False,
        "treatment_preference": "oral",
        "routine_consistency": "high",
        "priority_factor": "efficacy",
    }

    return [
        {
            "name": "canonical_hypertension_case",
            "payload": base,
            "decision_path": "topical_treatment",
            "status": "DECIDED",
            "expected_flags": ["HIGH_BLOOD_PRESSURE"],
            "expected_excluded_options": ["oral_treatment"],
            "rationale_primary_contains": "safest deterministic starting path",
            "rationale_safety_contains": "high blood pressure",
        },
        {
            "name": "cardiovascular_manual_review_case",
            "payload": cardiovascular_case,
            "decision_path": "manual_review",
            "status": "DECIDED",
            "expected_flags": ["CARDIOVASCULAR_CONDITION"],
            "expected_excluded_options": ["oral_treatment"],
            "rationale_primary_contains": "not appropriate",
            "rationale_safety_contains": "deterministic safety posture",
        },
        {
            "name": "prior_treatment_side_effects_case",
            "payload": side_effect_case,
            "decision_path": "manual_review",
            "status": "DECIDED",
            "expected_flags": ["PRIOR_SIDE_EFFECTS"],
            "expected_excluded_options": [],
            "rationale_primary_contains": "not appropriate",
            "rationale_safety_contains": "SAFETY flags present".lower(),
        },
        {
            "name": "missing_information_case",
            "payload": missing_info_case,
            "decision_path": "needs_more_information",
            "status": "NEEDS_MORE_INFO",
            "expected_flags": [],
            "expected_excluded_options": [],
            "rationale_primary_contains": "not enough information",
            "rationale_safety_contains": None,
        },
        {
            "name": "support_path_case",
            "payload": support_case,
            "decision_path": "topical_treatment_with_support",
            "status": "DECIDED",
            "expected_flags": ["SCALP_SENSITIVITY"],
            "expected_excluded_options": [],
            "rationale_primary_contains": "additional support",
            "rationale_safety_contains": "SAFETY flags present".lower(),
        },
        {
            "name": "convenience_priority_support_case",
            "payload": convenience_support_case,
            "decision_path": "topical_treatment_with_support",
            "status": "DECIDED",
            "expected_flags": [],
            "expected_excluded_options": [],
            "rationale_primary_contains": "additional support",
            "rationale_safety_contains": None,
        },
        {
            "name": "simpler_routine_preference_support_case",
            "payload": simpler_routine_preference_case,
            "decision_path": "topical_treatment_with_support",
            "status": "DECIDED",
            "expected_flags": [],
            "expected_excluded_options": [],
            "rationale_primary_contains": "additional support",
            "rationale_safety_contains": None,
        },
        {
            "name": "oral_preference_oral_treatment_case",
            "payload": oral_preference_topical_case,
            "decision_path": "oral_treatment",
            "status": "DECIDED",
            "expected_flags": [],
            "expected_excluded_options": [],
            "rationale_primary_contains": "oral treatment selected",
            "rationale_safety_contains": None,
        },
    ]
