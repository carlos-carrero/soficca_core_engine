from __future__ import annotations

from typing import Any, Dict, List

from pen_hair_v1.constants import (
    RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW,
    RULE_DEFAULT_SAFEST_START,
    RULE_EXCLUDE_ORAL_FOR_HYPERTENSION,
    RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS,
    RULE_ORAL_TREATMENT_PREFERENCE_SELECTED,
    RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW,
    RULE_SUPPORT_PATH_COMFORT_PRIORITY,
    RULE_SUPPORT_PATH_LOW_CONSISTENCY,
    RULE_SUPPORT_PATH_SCALP_SENSITIVITY,
    RULE_SUPPORT_PATH_SIMPLER_ROUTINE_PREFERENCE,
)
from pen_hair_v1.schema import PenNormalizedIntake


def build_trace_evidence(intake: PenNormalizedIntake) -> Dict[str, Any]:
    return {
        "high_blood_pressure": {
            "value": "true" if intake.high_blood_pressure else "false",
            "reason": "Explicitly provided by intake payload.",
        },
        "cardiovascular_conditions": {
            "value": "true" if intake.cardiovascular_conditions else "false",
            "reason": "Explicit yes/no cardiovascular risk signal from intake payload.",
        },
        "prior_treatment_use": {
            "value": "true" if intake.prior_treatment_use else "false",
            "reason": "Used for deterministic side-effect safety branching.",
        },
        "had_side_effects": {
            "value": "true" if intake.had_side_effects else "false",
            "reason": "Used for deterministic side-effect safety branching.",
        },
        "scalp_sensitivities": {
            "value": "true" if intake.scalp_sensitivities else "false",
            "reason": "Used for support-path selection.",
        },
        "routine_consistency": {
            "value": intake.routine_consistency,
            "reason": "Used for support-path or missing-info branching.",
        },
        "priority_factor": {
            "value": intake.priority_factor,
            "reason": "Used for comfort-priority support branching.",
        },
        "treatment_preference": {
            "value": intake.treatment_preference,
            "reason": "Used for missing-info guardrail branching and simpler-routine support branching.",
        },
    }


def rules_evaluated() -> List[str]:
    return [
        RULE_EXCLUDE_ORAL_FOR_HYPERTENSION,
        RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW,
        RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW,
        RULE_SUPPORT_PATH_SCALP_SENSITIVITY,
        RULE_SUPPORT_PATH_LOW_CONSISTENCY,
        RULE_SUPPORT_PATH_COMFORT_PRIORITY,
        RULE_SUPPORT_PATH_SIMPLER_ROUTINE_PREFERENCE,
        RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS,
        RULE_ORAL_TREATMENT_PREFERENCE_SELECTED,
        RULE_DEFAULT_SAFEST_START,
    ]
