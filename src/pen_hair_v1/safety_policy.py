from __future__ import annotations

from typing import Dict, List

from pen_hair_v1.constants import (
    EXCLUDED_OPTION_ORAL_TREATMENT,
    RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW,
    SAFETY_FLAG_HIGH_BLOOD_PRESSURE,
    SAFETY_FLAG_CARDIOVASCULAR_CONDITION,
    SAFETY_FLAG_PRIOR_SIDE_EFFECTS,
    SAFETY_FLAG_SCALP_SENSITIVITY,
)
from pen_hair_v1.schema import PenNormalizedIntake


def evaluate_safety(intake: PenNormalizedIntake) -> Dict[str, List[str]]:
    excluded_options: List[str] = []
    flags: List[str] = []
    safety_reasons: List[str] = []
    safety_rules_triggered: List[str] = []

    if intake.high_blood_pressure:
        excluded_options.append(EXCLUDED_OPTION_ORAL_TREATMENT)
        flags.append(SAFETY_FLAG_HIGH_BLOOD_PRESSURE)
        safety_reasons.append("High blood pressure present; oral treatment is excluded.")

    if intake.cardiovascular_conditions:
        if EXCLUDED_OPTION_ORAL_TREATMENT not in excluded_options:
            excluded_options.append(EXCLUDED_OPTION_ORAL_TREATMENT)
        flags.append(SAFETY_FLAG_CARDIOVASCULAR_CONDITION)
        safety_reasons.append("Cardiovascular condition(s) reported; clinician review required before oral treatment.")
        safety_rules_triggered.append(RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW)

    if intake.prior_treatment_use and intake.had_side_effects:
        flags.append(SAFETY_FLAG_PRIOR_SIDE_EFFECTS)
        safety_reasons.append("Prior treatment side effects reported; constrained safe routing required.")

    if intake.scalp_sensitivities:
        flags.append(SAFETY_FLAG_SCALP_SENSITIVITY)
        safety_reasons.append("Scalp sensitivity reported; comfort-first support is needed for topical plan.")

    unique_flags: List[str] = []
    for flag in flags:
        if flag not in unique_flags:
            unique_flags.append(flag)

    return {
        "excluded_options": excluded_options,
        "flags": unique_flags,
        "safety_reasons": safety_reasons,
        "safety_rules_triggered": safety_rules_triggered,
    }
