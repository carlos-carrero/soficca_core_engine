from __future__ import annotations

from typing import Any, Dict, List

from pydantic import ValidationError

from cardio_triage_v1.constants import (
    ALL_PATH_IDS,
    ALL_POLICY_RULE_IDS,
    ALL_RULE_IDS,
    CONTRACT_VERSION,
    DECISION_NEEDS_MORE_INFO,
    ENGINE_VERSION,
    RULESET_VERSION,
    SAFETY_CLEAR,
    SAFETY_ACTION_NONE,
    SAFETY_POLICY_VERSION,
)
from cardio_triage_v1.schema import CardioReport


def build_base_report() -> Dict[str, Any]:
    """Build a deterministic cardio v1 scaffold report and validate it."""
    report = {
        "ok": True,
        "errors": [],
        "versions": {
            "engine": ENGINE_VERSION,
            "ruleset": RULESET_VERSION,
            "safety_policy": SAFETY_POLICY_VERSION,
            "contract": CONTRACT_VERSION,
        },
        "decision": {
            "status": DECISION_NEEDS_MORE_INFO,
            "path": None,
            "flags": [],
            "reasons": [],
            "recommendations": [],
            "required_fields": [],
            "missing_fields": [],
            "decision_id": "UNDECIDED",
            "case_status": "PENDING_DATA",
            "decision_type": DECISION_NEEDS_MORE_INFO,
            "recommended_route": None,
            "urgency_level": "UNKNOWN",
            "clinical_summary": "Insufficient data for safe triage.",
            "required_actions": ["Provide missing critical cardio fields."],
        },
        "safety": {
            "status": SAFETY_CLEAR,
            "action": SAFETY_ACTION_NONE,
            "triggers": [],
            "policy_version": SAFETY_POLICY_VERSION,
            "safety_id": "NONE",
            "has_red_flags": False,
            "override_applied": False,
            "severity": "NONE",
            "flags": [],
        },
        "trace": {
            "policy_trace": {
                "evaluated": list(ALL_POLICY_RULE_IDS),
                "triggered": [],
            },
            "rules_evaluated": list(ALL_RULE_IDS),
            "rules_triggered": [],
            "evidence": {},
            "uncertainty_notes": ["Scaffold only: clinical logic not implemented."],
            "missing_fields": [],
            "activated_rules": [],
            "preliminary_route": None,
            "final_route": None,
            "override_reason": None,
            "conflicts_detected": [],
        },
    }
    return CardioReport.model_validate(report).model_dump(mode="python")


def assert_valid_report(report: Dict[str, Any]) -> CardioReport:
    """Validate and return a strongly typed cardio report model."""
    return CardioReport.model_validate(report)


def validate_report(report: Dict[str, Any]) -> List[str]:
    """Validate stable cardio v1 output shape and deterministic IDs."""
    problems: List[str] = []

    try:
        model = CardioReport.model_validate(report)
    except ValidationError as exc:
        for err in exc.errors(include_url=False):
            loc = ".".join(str(part) for part in err.get("loc", [])) or "$"
            msg = err.get("msg", "validation error")
            problems.append(f"{loc}: {msg}")
        return problems

    if model.versions.contract != CONTRACT_VERSION:
        problems.append("versions.contract must match canonical CONTRACT_VERSION")

    if model.decision.path is not None and model.decision.path.value not in ALL_PATH_IDS:
        problems.append("decision.path invalid")

    if model.decision.recommended_route is not None and model.decision.recommended_route.value not in ALL_PATH_IDS:
        problems.append("decision.recommended_route invalid")

    if model.trace.preliminary_route is not None and model.trace.preliminary_route.value not in ALL_PATH_IDS:
        problems.append("trace.preliminary_route invalid")

    if model.trace.final_route is not None and model.trace.final_route.value not in ALL_PATH_IDS:
        problems.append("trace.final_route invalid")

    return problems
