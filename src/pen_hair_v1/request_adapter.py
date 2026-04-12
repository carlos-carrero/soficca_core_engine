from __future__ import annotations

from typing import Any, Dict, Mapping

from pen_hair_v1.schema import PenIntakeRequest


_FRONTEND_TO_CANONICAL_KEYS: Dict[str, str] = {
    "norwoodStage": "norwood_stage",
    "lossNoticed": "loss_noticed",
    "lossAreas": "loss_areas",
    "mainGoal": "main_goal",
    "highBloodPressure": "high_blood_pressure",
    "cardiovascularConditions": "cardiovascular_conditions",
    "currentMedication": "current_medication",
    "medicationDetail": "medication_detail",
    "priorTreatmentUse": "prior_treatment_use",
    "whichTreatment": "which_treatment",
    "hadSideEffects": "had_side_effects",
    "sideEffectDetail": "side_effect_detail",
    "scalpSensitivities": "scalp_sensitivities",
    "scalpDetail": "scalp_detail",
    "treatmentPreference": "treatment_preference",
    "routineConsistency": "routine_consistency",
    "priorityFactor": "priority_factor",
    "baselinePhotosUploaded": "baseline_photos_uploaded",
}


def map_frontend_intake_to_request(frontend_intake: Mapping[str, Any]) -> PenIntakeRequest:
    """Map frontend IntakeData-like payloads (camelCase or snake_case) to canonical PenIntakeRequest.

    This mapper performs key translation only; it does not infer missing clinical signals.
    """
    canonical_payload: Dict[str, Any] = {}
    for key, value in frontend_intake.items():
        canonical_payload[_FRONTEND_TO_CANONICAL_KEYS.get(key, key)] = value

    return PenIntakeRequest.model_validate(canonical_payload)
