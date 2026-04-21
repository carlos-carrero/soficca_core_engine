from __future__ import annotations

from typing import List

from pen_hair_v1.constants import (
    DECISION_PATH_MANUAL_REVIEW,
    DECISION_PATH_NEEDS_MORE_INFORMATION,
    DECISION_PATH_ORAL_TREATMENT,
    DECISION_PATH_TOPICAL_TREATMENT,
    DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT,
)
from pen_hair_v1.schema import DecisionRationale, PenDecision, PenNormalizedIntake


def _format_safety_summary(decision: PenDecision) -> str | None:
    if decision.excluded_options:
        excluded = ", ".join(option.value for option in decision.excluded_options)
        if "HIGH_BLOOD_PRESSURE" in decision.flags:
            return f"{excluded} excluded due to high blood pressure safety posture."
        return f"{excluded} excluded due to deterministic safety posture."
    if decision.flags:
        return "Safety flags present: " + ", ".join(decision.flags)
    return None


def build_decision_rationale(decision: PenDecision, intake: PenNormalizedIntake) -> DecisionRationale:
    safety_summary = _format_safety_summary(decision)

    if decision.decision_path.value == DECISION_PATH_NEEDS_MORE_INFORMATION:
        return DecisionRationale(
            primary_reason="Not enough information for safe deterministic path selection.",
            supporting_reasons=[
                "One or more critical preference/consistency inputs are unknown.",
            ],
            safety_summary=safety_summary,
            why_not_selected=[
                "Topical and manual routes are deferred until missing critical inputs are clarified.",
            ],
        )

    if decision.decision_path.value == DECISION_PATH_MANUAL_REVIEW:
        return DecisionRationale(
            primary_reason="Automatic path selection is not appropriate for this case.",
            supporting_reasons=[
                "Deterministic risk guardrail triggered manual review.",
            ],
            safety_summary=safety_summary,
            why_not_selected=[
                "Oral treatment not auto-selected due to safety guardrails.",
                "Topical auto-confirmation deferred pending clinician review.",
            ],
        )

    if decision.decision_path.value == DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT:
        support_reasons: List[str] = []
        if intake.scalp_sensitivities:
            support_reasons.append("Scalp sensitivity indicates comfort-first onboarding support.")
        if intake.routine_consistency in {"low", "inconsistent", "variable"}:
            support_reasons.append("Routine consistency indicates adherence support is needed.")
        if intake.priority_factor in {"comfort", "tolerance", "minimize_side_effects", "side_effects"}:
            support_reasons.append("Priority factor emphasizes comfort/tolerability.")
        if intake.priority_factor in {"convenience", "simple", "simplicity", "easy_routine"}:
            support_reasons.append("Priority factor emphasizes convenience/simplicity.")
        if intake.treatment_preference in {"simple", "simplicity", "simpler_routine", "easy_routine", "minimal_steps"}:
            support_reasons.append("Treatment preference asks for a simpler routine with onboarding support.")

        return DecisionRationale(
            primary_reason="Topical treatment is appropriate with additional support framing.",
            supporting_reasons=support_reasons or ["Deterministic support criteria triggered."],
            safety_summary=safety_summary,
            why_not_selected=[
                "Oral treatment not selected as first path under current safety/profile constraints.",
            ],
        )

    if decision.decision_path.value == DECISION_PATH_ORAL_TREATMENT:
        oral_supporting: List[str] = []
        if intake.routine_consistency == "high":
            oral_supporting.append("High routine consistency supports reliable oral treatment adherence.")
        if intake.priority_factor == "efficacy":
            oral_supporting.append("Efficacy-focused priority aligns with oral treatment outcomes.")
        return DecisionRationale(
            primary_reason="Oral treatment selected per explicit preference with no medical contraindications.",
            supporting_reasons=oral_supporting or ["Oral treatment preference confirmed with no medical blockers."],
            safety_summary=safety_summary,
            why_not_selected=[
                "Topical treatment was not selected; patient preference for oral treatment was respected.",
            ],
        )

    supporting: List[str] = []
    if intake.treatment_preference == "topical":
        supporting.append("Patient preference aligns with a topical pathway.")
    if intake.routine_consistency == "high":
        supporting.append("Routine consistency supports reliable topical adherence.")

    return DecisionRationale(
        primary_reason="Topical treatment selected as safest deterministic starting path.",
        supporting_reasons=supporting,
        safety_summary=safety_summary,
        why_not_selected=[
            "Oral treatment excluded or not selected under deterministic safety posture.",
        ],
    )
