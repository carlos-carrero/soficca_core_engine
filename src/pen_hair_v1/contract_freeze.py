from __future__ import annotations

from typing import Any, Dict, List, Set

STABLE_TOP_LEVEL_KEYS: Set[str] = {
    "versions",
    "decision",
    "decision_rationale",
    "trace",
    "journey_views",
    "frontend_adapter",
}

STABLE_DECISION_KEYS: Set[str] = {
    "status",
    "decision_path",
    "title",
    "explanation",
    "flags",
    "excluded_options",
}

STABLE_RATIONALE_KEYS: Set[str] = {
    "primary_reason",
    "supporting_reasons",
    "safety_summary",
    "why_not_selected",
}

STABLE_JOURNEY_STATES: Set[str] = {"month_0", "week_6", "month_3", "month_6"}


def validate_frozen_pen_contract_shape(response: Dict[str, Any]) -> List[str]:
    issues: List[str] = []

    top_level_keys = set(response.keys())
    missing_top_level = STABLE_TOP_LEVEL_KEYS - top_level_keys
    if missing_top_level:
        issues.append(f"missing top-level keys: {sorted(missing_top_level)}")

    decision = response.get("decision", {})
    if isinstance(decision, dict):
        missing_decision = STABLE_DECISION_KEYS - set(decision.keys())
        if missing_decision:
            issues.append(f"missing decision keys: {sorted(missing_decision)}")
    else:
        issues.append("decision must be an object")

    rationale = response.get("decision_rationale", {})
    if isinstance(rationale, dict):
        missing_rationale = STABLE_RATIONALE_KEYS - set(rationale.keys())
        if missing_rationale:
            issues.append(f"missing decision_rationale keys: {sorted(missing_rationale)}")
    else:
        issues.append("decision_rationale must be an object")

    journey_views = response.get("journey_views", {})
    if isinstance(journey_views, dict):
        missing_journey = STABLE_JOURNEY_STATES - set(journey_views.keys())
        if missing_journey:
            issues.append(f"missing journey_views states: {sorted(missing_journey)}")
    else:
        issues.append("journey_views must be an object")

    frontend_adapter = response.get("frontend_adapter", {})
    if isinstance(frontend_adapter, dict):
        if "evaluation" not in frontend_adapter:
            issues.append("frontend_adapter.evaluation missing")
        if "journey" not in frontend_adapter:
            issues.append("frontend_adapter.journey missing")
        journey_adapter = frontend_adapter.get("journey", {})
        if isinstance(journey_adapter, dict):
            missing_adapter_states = STABLE_JOURNEY_STATES - set(journey_adapter.keys())
            if missing_adapter_states:
                issues.append(f"missing frontend_adapter.journey states: {sorted(missing_adapter_states)}")
        else:
            issues.append("frontend_adapter.journey must be an object")
    else:
        issues.append("frontend_adapter must be an object")

    return issues
