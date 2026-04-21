from __future__ import annotations

from typing import Dict, List, Set

from pen_hair_v1.constants import (
    DECISION_PATH_MANUAL_REVIEW,
    DECISION_PATH_NEEDS_MORE_INFORMATION,
    DECISION_PATH_ORAL_TREATMENT,
    DECISION_PATH_TOPICAL_TREATMENT,
    DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT,
    RULE_DEFAULT_SAFEST_START,
    RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS,
    RULE_ORAL_TREATMENT_PREFERENCE_SELECTED,
    RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW,
    RULE_SUPPORT_PATH_COMFORT_PRIORITY,
    RULE_SUPPORT_PATH_LOW_CONSISTENCY,
    RULE_SUPPORT_PATH_SCALP_SENSITIVITY,
    RULE_SUPPORT_PATH_SIMPLER_ROUTINE_PREFERENCE,
)
from pen_hair_v1.schema import PenNormalizedIntake

_UNKNOWN_VALUES: Set[str] = {
    "",
    "unknown",
    "unsure",
    "not_sure",
    "not sure",
    "n/a",
    "na",
    "prefer_not_to_say",
    "prefer not to say",
}
_LOW_CONSISTENCY_VALUES: Set[str] = {"low", "inconsistent", "variable"}
_COMFORT_PRIORITY_VALUES: Set[str] = {
    "comfort",
    "tolerance",
    "minimize_side_effects",
    "side_effects",
    "convenience",
    "simple",
    "simplicity",
    "easy_routine",
}
_SIMPLER_ROUTINE_PREFERENCE_VALUES: Set[str] = {
    "simple",
    "simplicity",
    "simpler_routine",
    "easy_routine",
    "minimal_steps",
}


def _has_critical_unknowns(intake: PenNormalizedIntake) -> bool:
    return (
        intake.treatment_preference in _UNKNOWN_VALUES
        or intake.routine_consistency in _UNKNOWN_VALUES
        or intake.priority_factor in _UNKNOWN_VALUES
    )


def select_decision_path(intake: PenNormalizedIntake, safety: Dict[str, List[str]]) -> Dict[str, object]:
    rules_triggered: List[str] = list(safety.get("safety_rules_triggered", []))
    excluded_options = list(safety.get("excluded_options", []))
    safety_reasons = list(safety.get("safety_reasons", []))

    if intake.cardiovascular_conditions:
        return {
            "decision_path": DECISION_PATH_MANUAL_REVIEW,
            "title": "Manual clinical review required",
            "explanation": "Reported cardiovascular conditions require clinician review before final treatment selection.",
            "rules_triggered": rules_triggered,
            "excluded_options": excluded_options,
        }

    if intake.prior_treatment_use and intake.had_side_effects:
        rules_triggered.append(RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW)
        return {
            "decision_path": DECISION_PATH_MANUAL_REVIEW,
            "title": "Manual review for prior side effects",
            "explanation": "Prior treatment-related side effects reported; manual review needed for safer next-step planning.",
            "rules_triggered": rules_triggered,
            "excluded_options": excluded_options,
        }

    if _has_critical_unknowns(intake):
        rules_triggered.append(RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS)
        return {
            "decision_path": DECISION_PATH_NEEDS_MORE_INFORMATION,
            "title": "More information needed",
            "explanation": "Decision-critical preference/consistency inputs are unknown; safe automatic selection is deferred.",
            "rules_triggered": rules_triggered,
            "excluded_options": excluded_options,
        }

    if intake.treatment_preference == "oral" and DECISION_PATH_ORAL_TREATMENT not in excluded_options:
        rules_triggered.append(RULE_ORAL_TREATMENT_PREFERENCE_SELECTED)
        return {
            "decision_path": DECISION_PATH_ORAL_TREATMENT,
            "title": "Oral treatment selected",
            "explanation": "Oral treatment preference selected with no medical contraindications detected.",
            "rules_triggered": rules_triggered,
            "excluded_options": excluded_options,
        }

    support_reasons: List[str] = []
    if intake.scalp_sensitivities:
        rules_triggered.append(RULE_SUPPORT_PATH_SCALP_SENSITIVITY)
        support_reasons.append("scalp sensitivity")

    if intake.routine_consistency in _LOW_CONSISTENCY_VALUES:
        rules_triggered.append(RULE_SUPPORT_PATH_LOW_CONSISTENCY)
        support_reasons.append("routine consistency support")

    if intake.priority_factor in _COMFORT_PRIORITY_VALUES:
        rules_triggered.append(RULE_SUPPORT_PATH_COMFORT_PRIORITY)
        support_reasons.append("comfort-first priority")

    if intake.treatment_preference in _SIMPLER_ROUTINE_PREFERENCE_VALUES:
        rules_triggered.append(RULE_SUPPORT_PATH_SIMPLER_ROUTINE_PREFERENCE)
        support_reasons.append("simpler-routine preference")

    if support_reasons:
        return {
            "decision_path": DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT,
            "title": "Topical plan with support",
            "explanation": "Topical treatment remains appropriate, with additional support for "
            + ", ".join(support_reasons)
            + ".",
            "rules_triggered": rules_triggered,
            "excluded_options": excluded_options,
        }

    rules_triggered.append(RULE_DEFAULT_SAFEST_START)
    title = "Topical first-line start"
    explanation_parts: List[str] = []
    if intake.treatment_preference == "oral":
        title = "Topical first-line start (oral preference deferred)"
        explanation_parts.append(
            "Oral preference was captured, but oral treatment is not auto-selected by this deterministic safety-first engine."
        )
    elif intake.treatment_preference == "topical":
        explanation_parts.append("Topical preference aligns with first-line deterministic routing.")

    explanation_parts.append("Topical treatment selected as safest deterministic starting path.")
    explanation = " ".join(explanation_parts)
    if safety_reasons:
        explanation = " ".join([*safety_reasons, *explanation_parts])

    return {
        "decision_path": DECISION_PATH_TOPICAL_TREATMENT,
        "title": title,
        "explanation": explanation,
        "rules_triggered": rules_triggered,
        "excluded_options": excluded_options,
    }
