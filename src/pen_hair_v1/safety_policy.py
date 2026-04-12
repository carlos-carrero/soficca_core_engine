from __future__ import annotations

from typing import Dict, List

from pen_hair_v1.constants import (
    EXCLUDED_OPTION_ORAL_TREATMENT,
    SAFETY_FLAG_HIGH_BLOOD_PRESSURE,
)
from pen_hair_v1.schema import PenNormalizedIntake


def evaluate_safety(intake: PenNormalizedIntake) -> Dict[str, List[str]]:
    excluded_options: List[str] = []
    flags: List[str] = []

    if intake.high_blood_pressure:
        excluded_options.append(EXCLUDED_OPTION_ORAL_TREATMENT)
        flags.append(SAFETY_FLAG_HIGH_BLOOD_PRESSURE)

    return {
        "excluded_options": excluded_options,
        "flags": flags,
    }
