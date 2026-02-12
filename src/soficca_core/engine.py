from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from soficca_core.validation import validate_input
from soficca_core.errors import make_error
from soficca_core.normalization import normalize
from soficca_core.rules import (
    apply_rules,
    PATH_ESCALATE_HUMAN,
    RULESET_VERSION,
    ALL_RULE_IDS,
)
from soficca_core.safety_policy import evaluate_safety, SAFETY_POLICY_VERSION, ALL_POLICY_RULE_IDS
from soficca_core.trace import TraceBuilder
from soficca_core.decision_contract import validate_report

ENGINE_VERSION = "0.3.0"

def _default_source(context: Dict[str, Any]) -> str:
    src = (context or {}).get("source")
    if src in ("USER", "DEVICE", "CLINICIAN", "UNKNOWN"):
        return src
    return "UNKNOWN"

def _build_base_report() -> Dict[str, Any]:
    return {
        "ok": True,
        "errors": [],
        "versions": {
            "engine": ENGINE_VERSION,
            "ruleset": RULESET_VERSION,
            "safety_policy": SAFETY_POLICY_VERSION,
        },
        "decision": {
            "status": "NEEDS_MORE_INFO",
            "path": None,
            "flags": [],
            "reasons": [],
            "recommendations": [],
            "required_fields": [],
        },
        "safety": {
            "status": "CLEAR",
            "action": "NONE",
            "triggers": [],
            "user_guidance_required_fields": [],
            "policy_version": SAFETY_POLICY_VERSION,
        },
        "trace": {
            "policy_trace": {"evaluated": [], "triggered": []},
            "rules_evaluated": [],
            "rules_triggered": [],
            "evidence": {},
            "uncertainty_notes": [],
        },
    }

def evaluate(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decision-first entrypoint. Deterministic and auditable."""
    base = _build_base_report()

    try:
        errors, cleaned = validate_input(input_data)
        if errors:
            base["ok"] = False
            base["errors"] = errors
            base["decision"]["status"] = "NEEDS_MORE_INFO"
            base["decision"]["required_fields"] = ["state"]
            base["trace"]["policy_trace"]["evaluated"] = list(ALL_POLICY_RULE_IDS)
            base["trace"]["rules_evaluated"] = list(ALL_RULE_IDS)
            return base

        state: Dict[str, Any] = cleaned["state"]
        context: Dict[str, Any] = cleaned["context"]
        src = _default_source(context)

        tb = TraceBuilder()

        # Evidence: record core fields (even if None)
        conflict_fields = set()
        conflicts = list(state.get("conflicts") or [])
        for c in conflicts:
            try:
                f = c.get("field")
                if f:
                    conflict_fields.add(str(f))
            except Exception:
                continue

        for key in ("frequency", "desire", "stress", "morning_erection", "wants_meds", "country", "safety_flags"):
            tb.add_evidence(
                key,
                value=state.get(key),
                source=src,
                recency_days=context.get("recency_days"),
                confidence=1.0 if key in state else None,
                contradiction=(key in conflict_fields),
            )

        # Policy evaluation (always)
        safety, policy_trace = evaluate_safety(state)
        for pid in ALL_POLICY_RULE_IDS:
            tb.add_policy_evaluated(pid)
        for pid in policy_trace.get("triggered") or []:
            tb.add_policy_triggered(pid)

        base["safety"] = safety

        # Rules evaluated list is complete by contract
        for rid in ALL_RULE_IDS:
            tb.add_rule_evaluated(rid)

        # If conflicts exist -> CONFLICT output
        if conflicts:
            base["decision"] = {
                "status": "CONFLICT",
                "path": None,
                "flags": [],
                "reasons": ["Conflicting evidence detected; cannot decide safely."],
                "recommendations": ["Resolve conflicting inputs, then re-run decision evaluation."],
                "required_fields": [],
            }
            tb.note_uncertainty("Conflict detected in inputs; decision withheld.")
            # Build trace and return (unless safety triggers, which overrides conflict)
            base["trace"] = tb.build()
            base["trace"]["policy_trace"] = policy_trace
            base["trace"]["rules_evaluated"] = tb.rules_evaluated
            base["trace"]["rules_triggered"] = tb.rules_triggered
            # Safety override takes precedence
            if safety.get("status") == "TRIGGERED":
                base["decision"] = {
                    "status": "ESCALATED",
                    "path": PATH_ESCALATE_HUMAN,
                    "flags": [],
                    "reasons": ["Safety policy triggered; escalation required."],
                    "recommendations": ["Escalate to human support / urgent care guidance."],
                    "required_fields": safety.get("user_guidance_required_fields") or [],
                }
            base["trace"] = tb.build()
            base["trace"]["policy_trace"] = policy_trace
            base["trace"]["rules_evaluated"] = list(ALL_RULE_IDS)
            base["trace"]["rules_triggered"] = tb.rules_triggered
            return _finalize(base)

        # Safety override
        if safety.get("status") == "TRIGGERED":
            base["decision"] = {
                "status": "ESCALATED",
                "path": PATH_ESCALATE_HUMAN,
                "flags": [],
                "reasons": ["Safety policy triggered; escalation required."],
                "recommendations": ["Escalate to human support / urgent care guidance."],
                "required_fields": safety.get("user_guidance_required_fields") or [],
            }
            tb.note_uncertainty("Safety override: clinical decision suppressed.")
            base["trace"] = tb.build()
            base["trace"]["policy_trace"] = policy_trace
            base["trace"]["rules_evaluated"] = list(ALL_RULE_IDS)
            base["trace"]["rules_triggered"] = []
            return _finalize(base)

        # Required fields logic (uncertainty)
        required: List[str] = []
        if state.get("frequency") is None:
            required.append("frequency")
        # If user wants meds pathway, require morning_erection for parallel eval gating
        if state.get("wants_meds") is True and state.get("morning_erection") is None:
            required.append("morning_erection")

        if required:
            base["decision"] = {
                "status": "NEEDS_MORE_INFO",
                "path": None,
                "flags": [],
                "reasons": ["Insufficient information to decide safely."],
                "recommendations": ["Collect the missing fields, then re-run decision evaluation."],
                "required_fields": required,
            }
            tb.note_uncertainty(f"Missing required fields: {', '.join(required)}.")
            base["trace"] = tb.build()
            base["trace"]["policy_trace"] = policy_trace
            base["trace"]["rules_evaluated"] = list(ALL_RULE_IDS)
            base["trace"]["rules_triggered"] = []
            return _finalize(base)

        # Apply deterministic rules
        signals = normalize(state)
        rules_decision = apply_rules(signals)

        triggered = list(rules_decision.get("rules_triggered") or [])
        for rid in triggered:
            tb.add_rule_triggered(rid)

        base["decision"] = {
            "status": "DECIDED",
            "path": rules_decision.get("path"),
            "flags": list(rules_decision.get("flags") or []),
            "reasons": list(rules_decision.get("reasons") or []),
            "recommendations": list(rules_decision.get("recommendations") or []),
            "required_fields": [],
        }

        base["trace"] = tb.build()
        base["trace"]["policy_trace"] = policy_trace
        base["trace"]["rules_evaluated"] = list(ALL_RULE_IDS)
        base["trace"]["rules_triggered"] = triggered

        return _finalize(base)

    except Exception as e:
        base["ok"] = False
        base["errors"] = [make_error("UNEXPECTED_ERROR", "Unexpected error while evaluating decision state", meta={"type": type(e).__name__})]
        # still include evaluated lists by contract
        base["trace"]["policy_trace"]["evaluated"] = list(ALL_POLICY_RULE_IDS)
        base["trace"]["rules_evaluated"] = list(ALL_RULE_IDS)
        return base

def _finalize(report: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure contract completeness: evaluated lists non-empty
    if not report["trace"]["policy_trace"]["evaluated"]:
        report["trace"]["policy_trace"]["evaluated"] = list(ALL_POLICY_RULE_IDS)
    if not report["trace"]["rules_evaluated"]:
        report["trace"]["rules_evaluated"] = list(ALL_RULE_IDS)

    # Validate contract (internal). If violated, mark as ok=False with error.
    problems = validate_report(report)
    if problems:
        report["ok"] = False
        report["errors"] = report.get("errors") or []
        report["errors"].append(make_error("CONTRACT_VIOLATION", "Decision report violates v0.3 contract", meta={"problems": problems}))

    # After assembling report
    decision = report.get("decision", {})

    if (
            decision.get("status") == "DECIDED"
            and decision.get("path") == "PATH_MORE_QUESTIONS"
            and not decision.get("required_fields")
    ):
        decision["path"] = None

    return report
