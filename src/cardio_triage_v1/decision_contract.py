from __future__ import annotations

from typing import Any, Dict, List

from cardio_triage_v1.constants import (
    ALL_PATH_IDS,
    ALL_POLICY_RULE_IDS,
    ALL_RULE_IDS,
    CONTRACT_VERSION,
    DECISION_NEEDS_MORE_INFO,
    DECISION_STATUSES,
    ENGINE_VERSION,
    PATH_ESCALATE_HUMAN,
    REPORT_TOP_LEVEL_KEYS,
    RULESET_VERSION,
    SAFETY_ACTION_NONE,
    SAFETY_ACTION_OVERRIDE_ESCALATE,
    SAFETY_ACTIONS,
    SAFETY_CLEAR,
    SAFETY_POLICY_VERSION,
    SAFETY_STATUSES,
)


def build_base_report() -> Dict[str, Any]:
    """Build a deterministic cardio v1 scaffold report (no clinical logic yet)."""
    return {
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
            "decision_id": "UNDECIDED",
        },
        "safety": {
            "status": SAFETY_CLEAR,
            "action": SAFETY_ACTION_NONE,
            "triggers": [],
            "policy_version": SAFETY_POLICY_VERSION,
            "safety_id": "NONE",
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
        },
    }


def validate_report(report: Dict[str, Any]) -> List[str]:
    """Validate stable cardio v1 output shape and deterministic IDs."""
    problems: List[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]

    for key in REPORT_TOP_LEVEL_KEYS:
        if key not in report:
            problems.append(f"missing field: {key}")

    versions = report.get("versions") or {}
    decision = report.get("decision") or {}
    safety = report.get("safety") or {}
    trace = report.get("trace") or {}
    policy_trace = trace.get("policy_trace") or {}

    for key in ("engine", "ruleset", "safety_policy", "contract"):
        if not isinstance(versions.get(key), str) or not versions.get(key):
            problems.append(f"versions.{key} must be non-empty string")

    if decision.get("status") not in DECISION_STATUSES:
        problems.append("decision.status invalid or missing")

    path = decision.get("path")
    if path is not None and path not in ALL_PATH_IDS:
        problems.append("decision.path invalid")

    for key in ("flags", "reasons", "recommendations", "required_fields"):
        if not isinstance(decision.get(key), list):
            problems.append(f"decision.{key} must be list")

    if not isinstance(decision.get("decision_id"), str):
        problems.append("decision.decision_id must be string")

    if safety.get("status") not in SAFETY_STATUSES:
        problems.append("safety.status invalid or missing")

    if safety.get("action") not in SAFETY_ACTIONS:
        problems.append("safety.action invalid or missing")

    for key in ("triggers",):
        if not isinstance(safety.get(key), list):
            problems.append(f"safety.{key} must be list")

    if not isinstance(safety.get("policy_version"), str):
        problems.append("safety.policy_version must be string")
    if not isinstance(safety.get("safety_id"), str):
        problems.append("safety.safety_id must be string")

    if not isinstance(policy_trace.get("evaluated"), list):
        problems.append("trace.policy_trace.evaluated must be list")
    if not isinstance(policy_trace.get("triggered"), list):
        problems.append("trace.policy_trace.triggered must be list")
    if not isinstance(trace.get("rules_evaluated"), list):
        problems.append("trace.rules_evaluated must be list")
    if not isinstance(trace.get("rules_triggered"), list):
        problems.append("trace.rules_triggered must be list")
    if not isinstance(trace.get("evidence"), dict):
        problems.append("trace.evidence must be object")
    if not isinstance(trace.get("uncertainty_notes"), list):
        problems.append("trace.uncertainty_notes must be list")

    if safety.get("status") == "TRIGGERED":
        if decision.get("status") != "ESCALATED":
            problems.append("If safety.TRIGGERED, decision.status must be ESCALATED")
        if decision.get("path") != PATH_ESCALATE_HUMAN:
            problems.append("If safety.TRIGGERED, decision.path must be PATH_ESCALATE_HUMAN")
        if safety.get("action") != SAFETY_ACTION_OVERRIDE_ESCALATE:
            problems.append("If safety.TRIGGERED, safety.action must be OVERRIDE_ESCALATE")

    return problems
