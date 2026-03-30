from __future__ import annotations

from typing import Any, Dict, List, Tuple

from cardio_triage_v1.constants import (
    CONFLICT_EXERTIONAL_WITHOUT_CHEST_PAIN,
    CONFLICT_PAIN_CHARACTER_WITHOUT_CHEST_PAIN,
    CONFLICT_PAIN_DURATION_WITHOUT_CHEST_PAIN,
    CONFLICT_PAIN_SEVERITY_WITHOUT_CHEST_PAIN,
    CONFLICT_RADIATION_WITHOUT_CHEST_PAIN,
    DEFERRED_PENDING_DATA,
    EMERGENCY_ROUTE,
    SAFETY_ACTION_OVERRIDE_ESCALATE,
    SAFETY_TRIGGERED,
)
from cardio_triage_v1.decision_contract import build_base_report
from cardio_triage_v1.normalization import normalize_for_readiness
from cardio_triage_v1.rules import apply_routing
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
        if field == "prior_mi_or_known_cad":
            if normalized_state.get("prior_mi") is None and normalized_state.get("known_cad") is None:
                missing.append(field)
            continue
        if field == "current_meds_summary_or_none":
            if value is not True:
                missing.append(field)
            continue
        if value is None or value == "":
            missing.append(field)

    return [f for f in CORE_REQUIRED_FIELDS if f in missing]


def detect_conflicts(normalized_state: Dict[str, Any]) -> List[str]:
    conflicts: List[str] = []

    chest_pain_present = normalized_state.get("chest_pain_present")
    if chest_pain_present is False:
        pain_severity = normalized_state.get("pain_severity")
        if pain_severity in {"mild", "moderate", "high", "severe"}:
            conflicts.append(CONFLICT_PAIN_SEVERITY_WITHOUT_CHEST_PAIN)

        pain_duration = normalized_state.get("pain_duration_minutes")
        if isinstance(pain_duration, int) and pain_duration > 0:
            conflicts.append(CONFLICT_PAIN_DURATION_WITHOUT_CHEST_PAIN)

        pain_character = normalized_state.get("pain_character")
        if pain_character not in {None, "none", "no_pain"}:
            conflicts.append(CONFLICT_PAIN_CHARACTER_WITHOUT_CHEST_PAIN)

        pain_radiation = normalized_state.get("pain_radiation")
        if pain_radiation not in {None, "none", "no_radiation"}:
            conflicts.append(CONFLICT_RADIATION_WITHOUT_CHEST_PAIN)

        if normalized_state.get("exertional_chest_pain") is True:
            conflicts.append(CONFLICT_EXERTIONAL_WITHOUT_CHEST_PAIN)

    # Deterministic de-duplication while preserving stable order
    ordered: List[str] = []
    for cid in conflicts:
        if cid not in ordered:
            ordered.append(cid)
    return ordered


def evaluate_readiness(input_data: Any) -> Dict[str, Any]:
    """Stage-5 deterministic readiness + conflict handling + routing + emergency override."""
    report = build_base_report()

    errors, cleaned = validate_input(input_data)
    if errors:
        report["ok"] = False
        report["errors"] = errors
        report["decision"]["status"] = "NEEDS_MORE_INFO"
        report["decision"]["decision_type"] = "NEEDS_MORE_INFO"
        report["decision"]["required_fields"] = ["state"]
        report["decision"]["missing_fields"] = ["state"]
        report["decision"]["clinical_summary"] = "Missing required structured state payload."
        report["decision"]["required_actions"] = ["Provide structured state object."]
        report["trace"]["missing_fields"] = ["state"]
        report["trace"]["uncertainty_notes"] = ["Missing required structured state payload."]
        report["trace"]["final_route"] = None
        return report

    normalized = normalize_for_readiness(cleaned["state"])
    missing_fields = get_missing_core_fields(normalized)

    report["trace"]["evidence"] = {k: {"value": v} for k, v in normalized.items()}

    if missing_fields:
        report["decision"]["status"] = "NEEDS_MORE_INFO"
        report["decision"]["decision_id"] = "READINESS_INCOMPLETE"
        report["decision"]["decision_type"] = "NEEDS_MORE_INFO"
        report["decision"]["case_status"] = "PENDING_DATA"
        report["decision"]["recommended_route"] = None
        report["decision"]["urgency_level"] = "UNKNOWN"
        report["decision"]["required_fields"] = list(missing_fields)
        report["decision"]["missing_fields"] = list(missing_fields)
        report["decision"]["clinical_summary"] = "Critical cardio fields missing; safe routing deferred."
        report["decision"]["required_actions"] = ["Collect all listed missing critical fields and resubmit."]
        report["trace"]["missing_fields"] = list(missing_fields)
        report["trace"]["uncertainty_notes"] = [
            "Critical cardio fields missing; triage logic not executed.",
        ]
        report["trace"]["preliminary_route"] = None
        report["trace"]["final_route"] = None
        return report

    conflicts_detected = detect_conflicts(normalized)
    report["trace"]["conflicts_detected"] = list(conflicts_detected)

    # Stage-4 deterministic preliminary route (non-emergency only)
    routing = apply_routing(normalized)
    report["decision"]["status"] = "DECIDED"
    report["decision"]["decision_id"] = routing["decision_id"]
    report["decision"]["decision_type"] = routing["decision_id"]
    report["decision"]["path"] = routing["preliminary_route"]
    report["decision"]["recommended_route"] = routing["preliminary_route"]
    report["decision"]["required_fields"] = []
    report["decision"]["missing_fields"] = []
    report["decision"]["reasons"] = list(routing["reasons"])
    report["decision"]["case_status"] = "TRIAGED"
    report["decision"]["urgency_level"] = "URGENT" if routing["decision_id"] == "URGENT_ESCALATION" else "ROUTINE"
    report["decision"]["clinical_summary"] = (
        "Urgent same-day review indicated by deterministic risk rule(s)."
        if routing["decision_id"] == "URGENT_ESCALATION"
        else "Stable complete case; routine review indicated by deterministic rules."
    )
    report["decision"]["required_actions"] = (
        ["Arrange same-day clinical escalation pathway."]
        if routing["decision_id"] == "URGENT_ESCALATION"
        else ["Schedule routine cardiology review."]
    )

    report["trace"]["missing_fields"] = []
    report["trace"]["uncertainty_notes"] = []
    report["trace"]["preliminary_route"] = routing["preliminary_route"]
    routed_rules = list(routing["rules_triggered"])
    report["trace"]["rules_triggered"] = routed_rules

    safety_eval = evaluate_safety(normalized)
    combined_activated_rules: List[str] = []
    for rid in routed_rules + list(safety_eval["activated_rules"]):
        if rid not in combined_activated_rules:
            combined_activated_rules.append(rid)
    report["trace"]["activated_rules"] = combined_activated_rules
    report["trace"]["override_reason"] = safety_eval["override_reason"]

    report["safety"]["has_red_flags"] = safety_eval["has_red_flags"]
    report["safety"]["override_applied"] = safety_eval["override_applied"]
    report["safety"]["severity"] = safety_eval["severity"]
    report["safety"]["flags"] = list(safety_eval["flags"])
    report["safety"]["triggers"] = list(safety_eval["activated_rules"])

    # Emergency override remains highest-priority
    if safety_eval["override_applied"]:
        report["decision"]["status"] = "ESCALATED"
        report["decision"]["path"] = EMERGENCY_ROUTE
        report["decision"]["decision_id"] = "EMERGENCY_OVERRIDE"
        report["decision"]["decision_type"] = "EMERGENCY_OVERRIDE"
        report["decision"]["recommended_route"] = EMERGENCY_ROUTE
        report["decision"]["case_status"] = "TRIAGED"
        report["decision"]["urgency_level"] = "EMERGENCY"
        report["decision"]["clinical_summary"] = "Hard emergency red-flag criteria met; emergency route required."
        report["decision"]["required_actions"] = ["Initiate immediate emergency escalation protocol."]
        report["decision"]["flags"] = list(safety_eval["flags"])
        report["safety"]["status"] = SAFETY_TRIGGERED
        report["safety"]["action"] = SAFETY_ACTION_OVERRIDE_ESCALATE
        report["safety"]["safety_id"] = "EMERGENCY_HARD_RED_FLAG"
        report["trace"]["final_route"] = EMERGENCY_ROUTE
    elif conflicts_detected:
        report["decision"]["status"] = "CONFLICT"
        report["decision"]["decision_id"] = DEFERRED_PENDING_DATA
        report["decision"]["decision_type"] = DEFERRED_PENDING_DATA
        report["decision"]["path"] = None
        report["decision"]["recommended_route"] = None
        report["decision"]["case_status"] = "PENDING_DATA"
        report["decision"]["urgency_level"] = "UNKNOWN"
        report["decision"]["clinical_summary"] = "Conflicting structured cardio inputs detected; safe routing deferred."
        report["decision"]["required_actions"] = [
            "Reconcile contradictory chest-pain fields.",
            "Reconfirm symptom presence, severity, and related attributes.",
        ]
        report["trace"]["uncertainty_notes"] = ["Conflicting structured inputs detected."]
        report["trace"]["final_route"] = None
    else:
        report["trace"]["final_route"] = routing["preliminary_route"]

    report["trace"]["policy_trace"]["triggered"] = list(safety_eval["activated_rules"])
    return report
