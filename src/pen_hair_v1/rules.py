from __future__ import annotations

from typing import Dict, List

from pen_hair_v1.constants import (
    DECISION_PATH_TOPICAL_TREATMENT,
    RULE_DEFAULT_SAFEST_START,
    RULE_EXCLUDE_ORAL_FOR_HYPERTENSION,
)
from pen_hair_v1.schema import PenNormalizedIntake


def select_decision_path(intake: PenNormalizedIntake, excluded_options: List[str]) -> Dict[str, object]:
    rules_triggered: List[str] = []

    if intake.high_blood_pressure:
        rules_triggered.append(RULE_EXCLUDE_ORAL_FOR_HYPERTENSION)

    rules_triggered.append(RULE_DEFAULT_SAFEST_START)

    return {
        "decision_path": DECISION_PATH_TOPICAL_TREATMENT,
        "title": "Topical first-line start",
        "explanation": "Oral treatment excluded due to high blood pressure; topical selected as safest starting path.",
        "rules_triggered": rules_triggered,
        "excluded_options": excluded_options,
    }
