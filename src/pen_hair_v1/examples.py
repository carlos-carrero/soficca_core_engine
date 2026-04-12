from __future__ import annotations

from typing import Any, Dict

from pen_hair_v1.request_adapter import map_frontend_intake_to_request
from pen_hair_v1.service import evaluate_pen_intake


def canonical_hypertension_request_example() -> Dict[str, Any]:
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


def canonical_hypertension_response_example() -> Dict[str, Any]:
    request = map_frontend_intake_to_request(canonical_hypertension_request_example())
    return evaluate_pen_intake(request).model_dump(mode="python")
