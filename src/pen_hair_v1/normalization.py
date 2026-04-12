from __future__ import annotations

from typing import Iterable, List, Optional

from pen_hair_v1.schema import PenIntakeRequest, PenNormalizedIntake


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def _normalize_unique_text_list(values: Iterable[str]) -> List[str]:
    normalized: List[str] = []
    for item in values:
        cleaned = _normalize_text(item)
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def normalize_intake(payload: PenIntakeRequest) -> PenNormalizedIntake:
    """Canonical deterministic normalization without implicit comorbidity assumptions."""
    return PenNormalizedIntake(
        age=payload.age,
        norwood_stage=payload.norwood_stage,
        loss_noticed=_normalize_text(payload.loss_noticed) or "",
        loss_areas=_normalize_unique_text_list(payload.loss_areas),
        main_goal=_normalize_text(payload.main_goal) or "",
        high_blood_pressure=payload.high_blood_pressure,
        cardiovascular_conditions=payload.cardiovascular_conditions,
        current_medication=payload.current_medication,
        medication_detail=_normalize_text(payload.medication_detail),
        prior_treatment_use=payload.prior_treatment_use,
        which_treatment=_normalize_text(payload.which_treatment),
        had_side_effects=payload.had_side_effects,
        side_effect_detail=_normalize_text(payload.side_effect_detail),
        scalp_sensitivities=payload.scalp_sensitivities,
        scalp_detail=_normalize_text(payload.scalp_detail),
        treatment_preference=_normalize_text(payload.treatment_preference) or "",
        routine_consistency=_normalize_text(payload.routine_consistency) or "",
        priority_factor=_normalize_text(payload.priority_factor) or "",
        baseline_photos_uploaded=payload.baseline_photos_uploaded,
    )
