from __future__ import annotations

from typing import Iterable, List

from pen_hair_v1.constants import (
    DECISION_PATH_MANUAL_REVIEW,
    DECISION_PATH_NEEDS_MORE_INFORMATION,
    DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT,
    RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW,
    RULE_EXCLUDE_ORAL_FOR_HYPERTENSION,
    RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS,
    RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW,
    RULE_SUPPORT_PATH_COMFORT_PRIORITY,
    RULE_SUPPORT_PATH_LOW_CONSISTENCY,
    RULE_SUPPORT_PATH_SCALP_SENSITIVITY,
    RULE_SUPPORT_PATH_SIMPLER_ROUTINE_PREFERENCE,
)
from pen_hair_v1.schema import JourneySection, JourneyView, PenJourneyViews


def _describe_primary_driver(decision_title: str, decision_path: str, rules_triggered: Iterable[str], flags: Iterable[str]) -> str:
    triggered = set(rules_triggered)
    flag_set = set(flags)
    if RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW in triggered:
        return "cardiovascular risk signal"
    if RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW in triggered:
        return "prior treatment side-effect signal"
    if RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS in triggered:
        return "missing critical preference/consistency inputs"
    if RULE_SUPPORT_PATH_SCALP_SENSITIVITY in triggered:
        return "scalp-sensitivity support signal"
    if RULE_SUPPORT_PATH_LOW_CONSISTENCY in triggered:
        return "routine-consistency support signal"
    if RULE_SUPPORT_PATH_SIMPLER_ROUTINE_PREFERENCE in triggered:
        return "simpler-routine support signal"
    if RULE_SUPPORT_PATH_COMFORT_PRIORITY in triggered:
        return "comfort/convenience support signal"
    if RULE_EXCLUDE_ORAL_FOR_HYPERTENSION in triggered or "HIGH_BLOOD_PRESSURE" in flag_set:
        return "blood-pressure oral-exclusion safety signal"
    if "oral preference deferred" in decision_title.lower():
        return "oral-preference deferral signal"
    if decision_path == DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT:
        return "support-path criteria"
    if decision_path == DECISION_PATH_MANUAL_REVIEW:
        return "manual-review guardrail"
    if decision_path == DECISION_PATH_NEEDS_MORE_INFORMATION:
        return "missing-information guardrail"
    return "deterministic first-line posture"


def _stage_specific_text(
    stage_key: str,
    decision_title: str,
    decision_path: str,
    primary_driver: str,
) -> tuple[str, str]:
    recommendation_body = f"{decision_title}. Continue topical protocol and monitor tolerance/progress at this milestone."
    narrative_body = (
        f"{stage_key} state: deterministic plan anchored to '{decision_title}', guided by {primary_driver}."
    )

    if decision_path == DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT:
        if stage_key == "month_0":
            recommendation_body = (
                f"Initiate topical plan with explicit support onboarding; primary support driver is {primary_driver}."
            )
            narrative_body = (
                "Activation stage: support-framed topical start to reduce friction and improve early adherence."
            )
        elif stage_key == "week_6":
            recommendation_body = (
                "Run early tolerance/adherence checkpoint and reinforce support prompts for the active support driver."
            )
            narrative_body = "Week-6 checkpoint stage: confirm comfort and consistency under support-path safeguards."
        elif stage_key == "month_3":
            recommendation_body = (
                "Assess continuation quality; keep support interventions that are improving adherence/comfort."
            )
            narrative_body = "Month-3 reassessment stage: maintain topical path while tuning support intensity."
        else:
            recommendation_body = (
                "Consolidate long-horizon support plan and define next follow-up cadence for sustained adherence."
            )
            narrative_body = "Month-6 consolidation stage: durable support strategy for long-term topical continuity."
    elif decision_path == DECISION_PATH_MANUAL_REVIEW:
        if stage_key == "month_0":
            recommendation_body = (
                f"Pause autonomous plan activation and queue clinician review for {primary_driver} before treatment commitment."
            )
            narrative_body = "Activation stage: manual-review hold is active pending clinician confirmation."
        elif stage_key == "week_6":
            recommendation_body = "Confirm review completion status and document clinician-approved safe next-step."
            narrative_body = "Week-6 checkpoint stage: manual-review workflow tracking and safety alignment."
        elif stage_key == "month_3":
            recommendation_body = "Re-check that post-review plan remains aligned with safety constraints and tolerability."
            narrative_body = "Month-3 reassessment stage: validate stability after manual review decisions."
        else:
            recommendation_body = "Lock long-horizon follow-up approach based on reviewed plan and risk posture."
            narrative_body = "Month-6 consolidation stage: maintain clinician-reviewed safety posture."
    elif decision_path == DECISION_PATH_NEEDS_MORE_INFORMATION:
        if stage_key == "month_0":
            recommendation_body = (
                "Collect missing preference/consistency details now; defer treatment activation until clarified."
            )
            narrative_body = "Activation stage: deterministic decision deferred due to unresolved critical inputs."
        elif stage_key == "week_6":
            recommendation_body = "Run follow-up intake checkpoint to close unresolved critical fields."
            narrative_body = "Week-6 checkpoint stage: unresolved critical inputs still block deterministic routing."
        elif stage_key == "month_3":
            recommendation_body = "Escalate data-completion outreach if key inputs remain unknown."
            narrative_body = "Month-3 reassessment stage: continued deferral without complete critical intake data."
        else:
            recommendation_body = "Set long-horizon next-step only after critical input completeness is achieved."
            narrative_body = "Month-6 consolidation stage: no final plan without deterministic input closure."
    else:
        if stage_key == "month_0":
            recommendation_body = f"Activate topical first-line plan under {primary_driver} with clear baseline capture."
            narrative_body = "Activation stage: first-line topical route selected under deterministic safety posture."
        elif stage_key == "week_6":
            recommendation_body = "Run early response/tolerance checkpoint and confirm adherence to first-line routine."
            narrative_body = "Week-6 checkpoint stage: verify early execution of the selected topical route."
        elif stage_key == "month_3":
            recommendation_body = "Reassess continuation confidence and maintain the deterministic topical course."
            narrative_body = "Month-3 reassessment stage: continue first-line topical plan with periodic review."
        else:
            recommendation_body = "Consolidate long-term maintenance plan and next-review cadence for topical continuity."
            narrative_body = "Month-6 consolidation stage: long-horizon topical direction under stable safety posture."

    return recommendation_body, narrative_body


def _build_view(
    stage_key: str,
    state_label: str,
    decision_title: str,
    decision_path: str,
    rules_triggered: List[str],
    flags: List[str],
) -> JourneyView:
    primary_driver = _describe_primary_driver(
        decision_title=decision_title,
        decision_path=decision_path,
        rules_triggered=rules_triggered,
        flags=flags,
    )
    recommendation_body, narrative_body = _stage_specific_text(
        stage_key=stage_key,
        decision_title=decision_title,
        decision_path=decision_path,
        primary_driver=primary_driver,
    )
    stage_badge = f"{stage_key} trace: {primary_driver}; rules={', '.join(rules_triggered) if rules_triggered else 'none'}"

    return JourneyView(
        hero=JourneySection(
            heading=state_label,
            body=f"{state_label}: {decision_title} selected under {primary_driver}.",
        ),
        progress_strip=["month_0", "week_6", "month_3", "month_6"],
        progress_photos={
            "requested": "front, top, temple",
            "status": "capture_or_update",
        },
        narrative=JourneySection(
            heading="Clinical narrative",
            body=narrative_body,
        ),
        recommendation=JourneySection(
            heading="Current recommendation",
            body=recommendation_body,
        ),
        decision_trace_badge=stage_badge,
    )


def build_journey_views(
    decision_title: str,
    decision_path: str,
    rules_triggered: List[str] | None = None,
    flags: List[str] | None = None,
) -> PenJourneyViews:
    resolved_rules = rules_triggered or []
    resolved_flags = flags or []
    return PenJourneyViews(
        month_0=_build_view(
            "month_0",
            "Baseline / Activation",
            decision_title,
            decision_path,
            resolved_rules,
            resolved_flags,
        ),
        week_6=_build_view(
            "week_6",
            "Week 6 Check-in",
            decision_title,
            decision_path,
            resolved_rules,
            resolved_flags,
        ),
        month_3=_build_view(
            "month_3",
            "Month 3 Progress",
            decision_title,
            decision_path,
            resolved_rules,
            resolved_flags,
        ),
        month_6=_build_view(
            "month_6",
            "Month 6 Review",
            decision_title,
            decision_path,
            resolved_rules,
            resolved_flags,
        ),
    )
