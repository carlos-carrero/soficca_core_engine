from __future__ import annotations

from typing import Any, Dict, List, Tuple

from cardio_triage_v1.constants import (
    EMERGENCY_ROUTE,
    SAFETY_ACTION_OVERRIDE_ESCALATE,
    SAFETY_TRIGGERED,
)
from cardio_triage_v1.decision_contract import build_base_report
from cardio_triage_v1.normalization import normalize_for_readiness
from cardio_triage_v1.safety_policy import evaluate_safety
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
        if field in {"prior_mi_or_known_cad", "current_meds_summary_or_none"}:
            if value is not True:
                missing.append(field)
            continue
        if value is None or value == "":
            missing.append(field)

    return [f for f in CORE_REQUIRED_FIELDS if f in missing]


def evaluate_readiness(input_data: Any) -> Dict[str, Any]:
    """Stage-3 deterministic readiness + hard emergency override.

    - Missing critical fields: return NEEDS_MORE_INFO (stage-2 behavior).
    - If complete: evaluate hard red flags and override to EMERGENCY_ROUTE when present.
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
        report["trace"]["uncertainty_notes"] = ["Missing required structured state payload."]
        report["trace"]["final_route"] = None
        return report

    normalized = normalize_for_readiness(cleaned["state"])
    missing_fields = get_missing_core_fields(normalized)

    report["trace"]["evidence"] = {k: {"value": v} for k, v in normalized.items()}
    report["trace"]["preliminary_route"] = None

    if missing_fields:
        report["decision"]["status"] = "NEEDS_MORE_INFO"
        report["decision"]["decision_id"] = "READINESS_INCOMPLETE"
        report["decision"]["required_fields"] = list(missing_fields)
        report["decision"]["missing_fields"] = list(missing_fields)
        report["trace"]["missing_fields"] = list(missing_fields)
        report["trace"]["uncertainty_notes"] = [
            "Critical cardio fields missing; triage logic not executed.",
        ]
        report["trace"]["final_route"] = None
        return report

    # Stage-2 baseline readiness complete
    report["decision"]["status"] = "DECIDED"
    report["decision"]["decision_id"] = "READINESS_COMPLETE"
    report["decision"]["required_fields"] = []
    report["decision"]["missing_fields"] = []
    report["trace"]["missing_fields"] = []
    report["trace"]["uncertainty_notes"] = []

    safety_eval = evaluate_safety(normalized)
    report["trace"]["activated_rules"] = list(safety_eval["activated_rules"])
    report["trace"]["override_reason"] = safety_eval["override_reason"]

    report["safety"]["has_red_flags"] = safety_eval["has_red_flags"]
    report["safety"]["override_applied"] = safety_eval["override_applied"]
    report["safety"]["severity"] = safety_eval["severity"]
    report["safety"]["flags"] = list(safety_eval["flags"])
    report["safety"]["triggers"] = list(safety_eval["activated_rules"])

    if safety_eval["override_applied"]:
        report["decision"]["status"] = "ESCALATED"
        report["decision"]["path"] = EMERGENCY_ROUTE
        report["decision"]["decision_id"] = "EMERGENCY_OVERRIDE"
        report["decision"]["flags"] = list(safety_eval["flags"])
        report["safety"]["status"] = SAFETY_TRIGGERED
        report["safety"]["action"] = SAFETY_ACTION_OVERRIDE_ESCALATE
        report["safety"]["safety_id"] = "EMERGENCY_HARD_RED_FLAG"
        report["trace"]["final_route"] = EMERGENCY_ROUTE
    else:
        report["trace"]["final_route"] = report["decision"].get("path")

    report["trace"]["policy_trace"]["triggered"] = list(safety_eval["activated_rules"])
    return report
