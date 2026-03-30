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


def normalize_for_readiness(state: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic extraction/coercion for stage-2 readiness checks only."""
    prior_mi = _coerce_bool(state.get("prior_mi"))
    known_cad = _coerce_bool(state.get("known_cad"))

    meds_summary = _coerce_non_empty_text(state.get("current_meds_summary"))
    meds_none = _coerce_bool(state.get("current_meds_none"))

    return {
        "age": _coerce_int(state.get("age")),
        "chest_pain_present": _coerce_bool(state.get("chest_pain_present")),
        "pain_duration_minutes": _coerce_int(state.get("pain_duration_minutes")),
        "pain_character": _coerce_non_empty_text(state.get("pain_character")),
        "pain_radiation": _coerce_non_empty_text(state.get("pain_radiation")),
        "dyspnea": _coerce_bool(state.get("dyspnea")),
        "syncope": _coerce_bool(state.get("syncope")),
        "systolic_bp": _coerce_int(state.get("systolic_bp")),
        "heart_rate": _coerce_int(state.get("heart_rate")),
        "prior_mi": prior_mi,
        "known_cad": known_cad,
        "prior_mi_or_known_cad": (prior_mi is not None) or (known_cad is not None),
        "current_meds_summary": meds_summary,
        "current_meds_none": meds_none,
        "current_meds_summary_or_none": (meds_summary is not None) or (meds_none is not None),
    }
