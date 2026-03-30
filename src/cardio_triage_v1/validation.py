from __future__ import annotations

from typing import Any, Dict, List, Tuple

from cardio_triage_v1.decision_contract import build_base_report
from cardio_triage_v1.normalization import normalize_for_readiness
from soficca_core.errors import make_error

CORE_REQUIRED_FIELDS: List[str] = [
    "age",
    "chest_pain_present",
    "pain_duration_minutes",
    "pain_character",
    "pain_radiation",
    "dyspnea",
    "syncope",
    "systolic_bp",
    "heart_rate",
    "prior_mi_or_known_cad",
    "current_meds_summary_or_none",
]


def validate_input(input_data: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Strict structured input validation for cardio v1 (no legacy chat mapping)."""
    errors: List[Dict[str, Any]] = []
    cleaned: Dict[str, Any] = {}

    if not isinstance(input_data, dict):
        errors.append(make_error("INVALID_TYPE", "Input data must be a dict", path="$"))
        return errors, cleaned

    state = input_data.get("state")
    context = input_data.get("context", {})

    if not isinstance(state, dict):
        errors.append(make_error("INVALID_STATE", "Input must include a 'state' object", path="$.state"))
        return errors, cleaned

    if not isinstance(context, dict):
        errors.append(make_error("INVALID_CONTEXT", "If provided, context must be an object", path="$.context"))
        return errors, cleaned

    cleaned["state"] = state
    cleaned["context"] = context
    return errors, cleaned


def get_missing_core_fields(normalized_state: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for field in CORE_REQUIRED_FIELDS:
        value = normalized_state.get(field)
        if value is None or value is False:
            # composite readiness fields are booleans where False means unavailable
            if field in {"prior_mi_or_known_cad", "current_meds_summary_or_none"}:
                missing.append(field)
            continue
        if value == "":
            missing.append(field)

    # explicit handling for scalar fields where zero can be valid, but None is not
    for scalar in (
        "age",
        "pain_duration_minutes",
        "systolic_bp",
        "heart_rate",
        "chest_pain_present",
        "dyspnea",
        "syncope",
        "pain_character",
        "pain_radiation",
    ):
        if scalar in CORE_REQUIRED_FIELDS and normalized_state.get(scalar) is None and scalar not in missing:
            missing.append(scalar)

    return [f for f in CORE_REQUIRED_FIELDS if f in missing]


def evaluate_readiness(input_data: Any) -> Dict[str, Any]:
    """Stage-2 deterministic readiness evaluation.

    - No triage routing logic yet.
    - Returns NEEDS_MORE_INFO when critical fields are missing.
    """
    report = build_base_report()

    errors, cleaned = validate_input(input_data)
    if errors:
        report["ok"] = False
        report["errors"] = errors
        report["decision"]["status"] = "NEEDS_MORE_INFO"
        report["decision"]["required_fields"] = ["state"]
        report["decision"]["missing_fields"] = ["state"]
        report["trace"]["missing_fields"] = ["state"]
        report["trace"]["uncertainty_notes"].append("Missing required structured state payload.")
        return report

    normalized = normalize_for_readiness(cleaned["state"])
    missing_fields = get_missing_core_fields(normalized)

    report["trace"]["evidence"] = {k: {"value": v} for k, v in normalized.items()}

    if missing_fields:
        report["decision"]["status"] = "NEEDS_MORE_INFO"
        report["decision"]["decision_id"] = "READINESS_INCOMPLETE"
        report["decision"]["required_fields"] = list(missing_fields)
        report["decision"]["missing_fields"] = list(missing_fields)
        report["trace"]["missing_fields"] = list(missing_fields)
        report["trace"]["uncertainty_notes"] = [
            "Critical cardio fields missing; triage logic not executed.",
        ]
        return report

    report["decision"]["status"] = "DECIDED"
    report["decision"]["decision_id"] = "READINESS_COMPLETE"
    report["decision"]["required_fields"] = []
    report["decision"]["missing_fields"] = []
    report["trace"]["missing_fields"] = []
    report["trace"]["uncertainty_notes"] = []
    return report
