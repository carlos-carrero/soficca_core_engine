from __future__ import annotations

from typing import Any, Dict, Optional


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _coerce_bool(value: Any) -> Optional[bool]:
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y", "1", "present"}:
            return True
        if lowered in {"false", "no", "n", "0", "none", "absent"}:
            return False
    return None


def _coerce_int(value: Any) -> Optional[int]:
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
            return int(stripped)
    return None


def _coerce_non_empty_text(value: Any) -> Optional[str]:
    if _is_missing(value):
        return None
    if isinstance(value, str):
        cleaned = value.strip().lower()
        return cleaned if cleaned else None
    return str(value).strip().lower() or None


def _risk_factor_count(state: Dict[str, Any]) -> Optional[int]:
    if isinstance(state.get("risk_factors"), list):
        return len([x for x in state.get("risk_factors") if not _is_missing(x)])
    explicit_count = _coerce_int(state.get("cv_risk_factors_count"))
    if isinstance(explicit_count, int) and explicit_count >= 0:
        return explicit_count
    return None


def normalize_for_readiness(state: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic extraction/coercion for readiness and routing checks."""
    prior_mi = _coerce_bool(state.get("prior_mi"))
    known_cad = _coerce_bool(state.get("known_cad"))

    meds_summary = _coerce_non_empty_text(state.get("current_meds_summary"))
    meds_none = _coerce_bool(state.get("current_meds_none"))

    pain_radiation = _coerce_non_empty_text(state.get("pain_radiation"))
    radiation_arm_or_jaw = pain_radiation in {"left_arm", "right_arm", "arm", "jaw", "neck"}

    return {
        "age": _coerce_int(state.get("age")),
        "chest_pain_present": _coerce_bool(state.get("chest_pain_present")),
        "pain_duration_minutes": _coerce_int(state.get("pain_duration_minutes")),
        "pain_character": _coerce_non_empty_text(state.get("pain_character")),
        "pain_severity": _coerce_non_empty_text(state.get("pain_severity")),
        "pain_radiation": pain_radiation,
        "radiation_arm_or_jaw": radiation_arm_or_jaw,
        "exertional_chest_pain": _coerce_bool(state.get("exertional_chest_pain")),
        "diaphoresis": _coerce_bool(state.get("diaphoresis")),
        "cv_risk_factors_count": _risk_factor_count(state),
        "dyspnea": _coerce_bool(state.get("dyspnea")),
        "syncope": _coerce_bool(state.get("syncope")),
        "systolic_bp": _coerce_int(state.get("systolic_bp")),
        "heart_rate": _coerce_int(state.get("heart_rate")),
        "prior_mi": prior_mi,
        "known_cad": known_cad,
        "prior_mi_or_known_cad": (prior_mi is True) or (known_cad is True),
        "current_meds_summary": meds_summary,
        "current_meds_none": meds_none,
        "current_meds_summary_or_none": (meds_summary is not None) or (meds_none is True),
    }
