from __future__ import annotations
from typing import Any, Dict, List, Optional

DECISION_STATUSES = {"DECIDED", "NEEDS_MORE_INFO", "CONFLICT", "ESCALATED"}
SAFETY_STATUSES = {"CLEAR", "TRIGGERED"}
SAFETY_ACTIONS = {"NONE", "OVERRIDE_ESCALATE", "OVERRIDE_BLOCK_RECS"}

def _as_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []

def validate_report(report: Dict[str, Any]) -> List[str]:
    """Return a list of contract violations (empty means valid)."""
    problems: List[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]

    for k in ("ok", "errors", "versions", "decision", "safety", "trace"):
        if k not in report:
            problems.append(f"missing field: {k}")

    # safety invariants
    safety = report.get("safety") or {}
    decision = report.get("decision") or {}
    trace = report.get("trace") or {}
    versions = report.get("versions") or {}

    if safety.get("status") not in SAFETY_STATUSES:
        problems.append("safety.status invalid or missing")
    if safety.get("action") not in SAFETY_ACTIONS:
        problems.append("safety.action invalid or missing")
    if not isinstance(safety.get("triggers"), list):
        problems.append("safety.triggers must be list")
    if not isinstance(safety.get("user_guidance_required_fields"), list):
        problems.append("safety.user_guidance_required_fields must be list")
    if not isinstance(safety.get("policy_version"), str):
        problems.append("safety.policy_version must be string")

    if decision.get("status") not in DECISION_STATUSES:
        problems.append("decision.status invalid or missing")

    # versions required
    for v in ("engine", "ruleset", "safety_policy"):
        if not isinstance(versions.get(v), str) or not versions.get(v):
            problems.append(f"versions.{v} must be non-empty string")

    # trace required
    policy_trace = (trace.get("policy_trace") or {})
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

    # invariant: if safety triggered, must escalate and set path
    if safety.get("status") == "TRIGGERED":
        if decision.get("status") != "ESCALATED":
            problems.append("If safety.TRIGGERED, decision.status must be ESCALATED")
        if decision.get("path") != "PATH_ESCALATE_HUMAN":
            problems.append("If safety.TRIGGERED, decision.path must be PATH_ESCALATE_HUMAN")

    # invariant: NEEDS_MORE_INFO requires required_fields non-empty
    if decision.get("status") == "NEEDS_MORE_INFO":
        rf = decision.get("required_fields")
        if not isinstance(rf, list) or len(rf) == 0:
            problems.append("If decision.NEEDS_MORE_INFO, decision.required_fields must be non-empty list")

    # invariant: CONFLICT requires uncertainty note
    if decision.get("status") == "CONFLICT":
        notes = _as_list(trace.get("uncertainty_notes"))
        if not any("conflict" in str(n).lower() for n in notes):
            problems.append("If decision.CONFLICT, trace.uncertainty_notes must mention conflict")

    return problems
