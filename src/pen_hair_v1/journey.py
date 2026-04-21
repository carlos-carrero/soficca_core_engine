from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from pen_hair_v1.constants import (
    DECISION_PATH_MANUAL_REVIEW,
    DECISION_PATH_NEEDS_MORE_INFORMATION,
    DECISION_PATH_ORAL_TREATMENT,
    DECISION_PATH_TOPICAL_TREATMENT,
    DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT,
    RULE_CARDIO_COMORBIDITY_MANUAL_REVIEW,
    RULE_EXCLUDE_ORAL_FOR_HYPERTENSION,
    RULE_NEEDS_MORE_INFORMATION_UNKNOWN_INPUTS,
    RULE_PRIOR_SIDE_EFFECTS_MANUAL_REVIEW,
    RULE_SUPPORT_PATH_COMFORT_PRIORITY,
    RULE_SUPPORT_PATH_LOW_CONSISTENCY,
    RULE_SUPPORT_PATH_SCALP_SENSITIVITY,
    RULE_SUPPORT_PATH_SIMPLER_ROUTINE_PREFERENCE,
    SAFETY_FLAG_HIGH_BLOOD_PRESSURE,
    SAFETY_FLAG_SCALP_SENSITIVITY,
)
from pen_hair_v1.schema import (
    FrontendJourneyAdapter,
    FrontendTreatmentDetails,
    FrontendJourneyHero,
    FrontendJourneyNarrative,
    FrontendJourneyRecommendation,
    FrontendJourneyTraceBadge,
    FrontendJourneyView,
    FrontendPhotoStep,
    FrontendProgressPhotos,
    FrontendProgressStrip,
    FrontendProgressStripItem,
    JourneySection,
    JourneyView,
    PenJourneyViews,
)


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
    if decision_path == DECISION_PATH_ORAL_TREATMENT:
        return "oral treatment preference signal"
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
            narrative_body = "Your topical treatment is now active with a structured support layer designed to improve comfort and adherence from the start. Your baseline has been captured."
        elif stage_key == "week_6":
            recommendation_body = (
                "Run early tolerance/adherence checkpoint and reinforce support prompts for the active support driver."
            )
            narrative_body = "Six weeks in. This checkpoint focuses on your comfort with the routine and early tolerance signals under the support framework."
        elif stage_key == "month_3":
            recommendation_body = (
                "Assess continuation quality; keep support interventions that are improving adherence/comfort."
            )
            narrative_body = "Three months in. Your support-guided topical protocol is being reviewed for comfort, adherence, and initial response quality."
        else:
            recommendation_body = (
                "Consolidate long-horizon support plan and define next follow-up cadence for sustained adherence."
            )
            narrative_body = "Six months completed. Your support-assisted topical plan has reached its first long-term milestone. Continue your routine as directed."
    elif decision_path == DECISION_PATH_MANUAL_REVIEW:
        if stage_key == "month_0":
            recommendation_body = (
                f"Pause autonomous plan activation and queue clinician review for {primary_driver} before treatment commitment."
            )
            narrative_body = "Your case requires clinician review before treatment can be selected. No active treatment is running until your review is complete."
        elif stage_key == "week_6":
            recommendation_body = "Confirm review completion status and document clinician-approved safe next-step."
            narrative_body = "Clinician review is still pending. No treatment milestone is available until your case is cleared for activation."
        elif stage_key == "month_3":
            recommendation_body = "Re-check that post-review plan remains aligned with safety constraints and tolerability."
            narrative_body = "Your case is still under review. Treatment continuation at the 3-month mark depends on resolution of your clinical assessment."
        else:
            recommendation_body = "Lock long-horizon follow-up approach based on reviewed plan and risk posture."
            narrative_body = "Manual review is outstanding. No long-term treatment direction can be confirmed without a completed clinical evaluation."
    elif decision_path == DECISION_PATH_NEEDS_MORE_INFORMATION:
        if stage_key == "month_0":
            recommendation_body = (
                "Collect missing preference/consistency details now; defer treatment activation until clarified."
            )
            narrative_body = "Your profile needs additional information before your case can be routed to a treatment. Please complete your intake to activate your plan."
        elif stage_key == "week_6":
            recommendation_body = "Run follow-up intake checkpoint to close unresolved critical fields."
            narrative_body = "Without a complete intake profile, no treatment checkpoint is available at this stage."
        elif stage_key == "month_3":
            recommendation_body = "Escalate data-completion outreach if key inputs remain unknown."
            narrative_body = "Your case cannot be assessed at the 3-month stage without a completed intake profile."
        else:
            recommendation_body = "Set long-horizon next-step only after critical input completeness is achieved."
            narrative_body = "A complete intake profile is required before any long-term treatment direction can be established."
    elif decision_path == DECISION_PATH_ORAL_TREATMENT:
        if stage_key == "month_0":
            recommendation_body = "Oral treatment initiated. Take as directed and monitor for tolerance and early response."
            narrative_body = "Your oral treatment is now active, based on your explicit preference and health profile. Your baseline has been recorded and your first checkpoint is in 6 weeks."
        elif stage_key == "week_6":
            recommendation_body = "Continue oral protocol. Run early response checkpoint to confirm tolerability and adherence."
            narrative_body = "Six weeks in. This checkpoint focuses on early adherence and tolerance signals from your oral treatment before your 3-month reassessment."
        elif stage_key == "month_3":
            recommendation_body = "Reassess oral treatment progress and confirm continuation plan with clinician review."
            narrative_body = "Three months in. Your oral treatment is progressing. Your clinician will review your response at this stage to confirm your ongoing plan."
        else:
            recommendation_body = "Consolidate long-term oral treatment maintenance and establish next-review cadence."
            narrative_body = "Six months completed. Your oral treatment plan has reached its first long-term milestone. Your next annual review will confirm your maintenance direction."
    else:
        is_safety_constrained = "blood-pressure" in primary_driver
        if stage_key == "month_0":
            recommendation_body = f"Activate topical first-line plan under {primary_driver} with clear baseline capture."
            if is_safety_constrained:
                narrative_body = "Your treatment has been selected under a safety-first posture. A topical route has been activated as your safe starting point based on your health profile. Your baseline has been captured."
            else:
                narrative_body = "Your topical treatment is now active, selected based on your case profile. Your baseline has been recorded and your first checkpoint is in 6 weeks."
        elif stage_key == "week_6":
            recommendation_body = "Run early response/tolerance checkpoint and confirm adherence to first-line routine."
            narrative_body = "Six weeks in. This checkpoint evaluates early adherence and tolerance signals from your topical routine before your 3-month reassessment."
        elif stage_key == "month_3":
            recommendation_body = "Reassess continuation confidence and maintain the deterministic topical course."
            if is_safety_constrained:
                narrative_body = "Three months in. Your topical plan is holding under a stable safety posture. Continue the current protocol."
            else:
                narrative_body = "Three months in. Your topical treatment response is being evaluated. Continue the current protocol unless your clinician advises a change."
        else:
            recommendation_body = "Consolidate long-term maintenance plan and next-review cadence for topical continuity."
            narrative_body = "Six months completed. Your topical treatment plan has reached its first long-term milestone. Continue your maintenance routine as directed."

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


_STAGE_HERO_TITLES: dict = {
    "month_0": "Your plan is ready",
    "week_6": "Your plan is active",
    "month_3": "Your plan is responding",
    "month_6": "Your plan is holding steady",
}

_STAGE_HERO_TITLES_DEFERRED: dict = {
    DECISION_PATH_MANUAL_REVIEW: "Your profile is under review",
    DECISION_PATH_NEEDS_MORE_INFORMATION: "Your profile needs more information",
}

_STAGE_SUBTITLES: dict = {
    "topical": {
        "month_0": "Your topical treatment plan has been selected based on your intake and health profile.",
        "week_6": "Your topical treatment is moving in the right direction. Early indicators look positive.",
        "month_3": "Three months of consistency. Your scalp is showing clear signs of response.",
        "month_6": "Six months completed. Your treatment response remains stable and within the expected range.",
    },
    "oral": {
        "month_0": "Your oral treatment plan has been selected based on your intake and health profile.",
        "week_6": "Your oral treatment is progressing. Early adherence and tolerance indicators look positive.",
        "month_3": "Three months of daily dosing. Your response indicators are within the expected range.",
        "month_6": "Six months completed. Your treatment response remains stable and within the expected range.",
    },
    "default": {
        "month_0": "Your starting path has been selected based on your intake and health profile.",
        "week_6": "Your case is currently under review. No active treatment milestone is tracked at this stage.",
        "month_3": "Your case is under review. Treatment direction will be confirmed once your profile is resolved.",
        "month_6": "No long-term treatment direction can be confirmed until your review is complete.",
    },
}

_STAGE_NEXT_REVIEW: dict = {
    "month_0": "in 6 weeks",
    "week_6": "in 8 weeks",
    "month_3": "in 4 weeks",
    "month_6": "annual review scheduled",
}

_STAGE_NARRATIVE_TITLES: dict = {
    "month_0": "How your plan begins",
    "week_6": "How your plan is going",
    "month_3": "How your plan is going",
    "month_6": "How your plan is going",
}

_PLAN_LABELS: dict = {
    DECISION_PATH_TOPICAL_TREATMENT: "Active plan: Topical treatment",
    DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT: "Active plan: Topical treatment + support",
    DECISION_PATH_ORAL_TREATMENT: "Active plan: Oral treatment",
    DECISION_PATH_MANUAL_REVIEW: "Status: Pending clinician review",
    DECISION_PATH_NEEDS_MORE_INFORMATION: "Status: Awaiting profile completion",
}

_TREATMENT_PLAN_LABELS: dict = {
    "topical_minoxidil": "Active plan: Topical Minoxidil 5%",
    "oral_finasteride": "Active plan: Oral Finasteride 1 mg",
    "oral_minoxidil": "Active plan: Oral Minoxidil",
}

_STAGE_CHECKPOINT_FOCUS: dict = {
    "month_0": "initial treatment selection",
    "week_6": "early adherence and tolerance",
    "month_3": "3-month response reassessment",
    "month_6": "long-term maintenance review",
}

_TREATMENT_LABEL_AND_ICON: dict = {
    "topical_minoxidil": {
        "product": "Topical Minoxidil 5%",
        "icon": "droplets",
    },
    "oral_finasteride": {
        "product": "Oral Finasteride 1 mg",
        "icon": "pill",
    },
    "oral_minoxidil": {
        "product": "Oral Minoxidil",
        "icon": "pill",
    },
}

_TREATMENT_STAGE_DESCRIPTIONS: dict = {
    "topical_minoxidil": {
        "month_0": "Starting today, applied directly to the scalp to stimulate follicles and establish your baseline response.",
        "week_6": "Continue your application routine. Consistency at this stage is the primary driver of a reliable early response.",
        "month_3": "Three months of consistent application. Your scalp response is building — maintain the current protocol.",
        "month_6": "Six months in. Topical Minoxidil 5% remains your active maintenance treatment going forward.",
    },
    "oral_finasteride": {
        "month_0": "Starting today, taken once daily to reduce DHT levels and slow hair loss at its hormonal source.",
        "week_6": "Continue your daily oral dose. Early adherence and tolerance monitoring are the key signals at this checkpoint.",
        "month_3": "Three months on oral Finasteride. Your DHT response is building — confirm continuation with your clinician.",
        "month_6": "Six months in. Oral Finasteride 1 mg remains your active long-term treatment under ongoing review.",
    },
    "oral_minoxidil": {
        "month_0": "Starting today, low-dose oral Minoxidil taken once daily to promote hair growth with a minimal topical footprint.",
        "week_6": "Continue your daily dose. Tolerance and early hair growth signals are the key indicators at this checkpoint.",
        "month_3": "Three months on oral Minoxidil. Reassess adherence and response and confirm continuation with your clinician.",
        "month_6": "Six months in. Oral Minoxidil remains your active treatment under ongoing clinical review.",
    },
}

_TREATMENT_DETAILS: dict = {
    "topical_minoxidil": {
        "route": "Topical",
        "cadence": "Once daily, applied directly to the scalp",
        "purpose": "Supports hair regrowth by stimulating follicles and extending the growth phase",
        "review_note": None,
    },
    "oral_finasteride": {
        "route": "Oral",
        "cadence": "Once daily",
        "purpose": "Reduces DHT-related hair loss progression by blocking its hormonal source",
        "review_note": None,
    },
    "oral_minoxidil": {
        "route": "Oral",
        "cadence": "Once daily, low-dose",
        "purpose": "Promotes hair growth with a minimal topical footprint; selected for its tolerability profile",
        "review_note": "Requires medical approval before treatment activation.",
    },
}

_SAFETY_PRIORITY_FACTORS = {"safety", "tolerance", "minimize_side_effects", "side_effects"}


def _determine_treatment_key(decision_path: str, priority_factor: str) -> str:
    if decision_path == DECISION_PATH_ORAL_TREATMENT:
        if priority_factor in _SAFETY_PRIORITY_FACTORS:
            return "oral_minoxidil"
        return "oral_finasteride"
    if decision_path in {DECISION_PATH_TOPICAL_TREATMENT, DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT}:
        return "topical_minoxidil"
    return ""


_STAGE_PROGRESS_ITEMS: dict = {
    "month_0": [
        {"label": "Plan status", "value": "Activated", "icon": "check"},
        {"label": "Baseline photos", "value": "Uploaded", "icon": "camera"},
        {"label": "Next milestone", "value": "Week 6 check-in", "icon": "target"},
    ],
    "week_6": [
        {"label": "Consistency", "value": "Strong this month", "icon": "activity"},
        {"label": "Latest update", "value": "Week 6 check-in", "icon": "calendar"},
        {"label": "Progress", "value": "Early stabilization", "icon": "trending"},
    ],
    "month_3": [
        {"label": "Consistency", "value": "Excellent", "icon": "activity"},
        {"label": "Latest update", "value": "Month 3 review", "icon": "calendar"},
        {"label": "Progress", "value": "Visible response", "icon": "trending"},
    ],
    "month_6": [
        {"label": "Consistency", "value": "Consistent", "icon": "activity"},
        {"label": "Latest update", "value": "Month 6 evaluation", "icon": "calendar"},
        {"label": "Progress", "value": "Sustained results", "icon": "trending"},
    ],
}

_ALL_PHOTO_STEPS = [
    {"id": "baseline", "label": "Baseline"},
    {"id": "week_6", "label": "Week 6"},
    {"id": "month_3", "label": "Month 3"},
    {"id": "month_6", "label": "Month 6"},
]

_STAGE_UNLOCKED_PHOTOS: dict = {
    "month_0": {"baseline"},
    "week_6": {"baseline", "week_6"},
    "month_3": {"baseline", "week_6", "month_3"},
    "month_6": {"baseline", "week_6", "month_3", "month_6"},
}

def _build_month0_treatment_description(
    treatment_key: str,
    flags: List[str],
    rules_triggered: List[str],
) -> str:
    if treatment_key == "topical_minoxidil":
        if SAFETY_FLAG_HIGH_BLOOD_PRESSURE in flags:
            return (
                "Selected as a topical-first option based on your safety profile. "
                "Oral treatment is not recommended due to high blood pressure. "
                "Applied directly to the scalp daily."
            )
        if SAFETY_FLAG_SCALP_SENSITIVITY in flags:
            return (
                "Selected with scalp-specific support to account for your reported sensitivity. "
                "Applied directly to the scalp daily with comfort-adjusted support."
            )
        return (
            "Selected as your first-line topical treatment based on your case profile. "
            "Applied directly to the scalp daily to stimulate follicles and establish your baseline response."
        )
    if treatment_key == "oral_finasteride":
        return (
            "Selected as a once-daily oral treatment aligned with your explicit treatment preference. "
            "Reduces DHT levels at their hormonal source to slow hair loss and support regrowth."
        )
    if treatment_key == "oral_minoxidil":
        return (
            "Selected as a safety-preferred oral option aligned with your tolerance priority. "
            "Low-dose once-daily dosing to promote hair growth with a minimal topical footprint."
        )
    return ""


def _build_frontend_view(
    stage_key: str,
    state_label: str,
    decision_title: str,
    decision_path: str,
    rules_triggered: List[str],
    flags: List[str],
    trace_evidence: Dict[str, Any] | None = None,
    treatment_key: str = "",
) -> FrontendJourneyView:
    primary_driver = _describe_primary_driver(
        decision_title=decision_title,
        decision_path=decision_path,
        rules_triggered=rules_triggered,
        flags=flags,
    )
    _, narrative_body = _stage_specific_text(
        stage_key=stage_key,
        decision_title=decision_title,
        decision_path=decision_path,
        primary_driver=primary_driver,
    )
    treatment_meta = _TREATMENT_LABEL_AND_ICON.get(treatment_key) if treatment_key else None
    show_recommendation = treatment_meta is not None
    requires_medical_approval = (treatment_key == "oral_minoxidil") and (stage_key == "month_0")
    _detail_data = _TREATMENT_DETAILS.get(treatment_key) if treatment_key else None
    treatment_details: Optional[FrontendTreatmentDetails] = (
        FrontendTreatmentDetails(**_detail_data) if _detail_data else None
    )
    if stage_key == "month_0" and treatment_key:
        treatment_description = _build_month0_treatment_description(treatment_key, flags, rules_triggered)
    else:
        treatment_description = (
            _TREATMENT_STAGE_DESCRIPTIONS.get(treatment_key, {}).get(stage_key)
            if treatment_key else None
        )
    unlocked_ids = _STAGE_UNLOCKED_PHOTOS[stage_key]
    photo_steps = [
        FrontendPhotoStep(id=step["id"], label=step["label"], unlocked=step["id"] in unlocked_ids)
        for step in _ALL_PHOTO_STEPS
    ]
    _subtitle_modality = (
        "oral" if treatment_key in {"oral_finasteride", "oral_minoxidil"}
        else ("topical" if treatment_key else "default")
    )
    subtitle = _STAGE_SUBTITLES[_subtitle_modality][stage_key]
    hero_title = _STAGE_HERO_TITLES_DEFERRED.get(decision_path, _STAGE_HERO_TITLES[stage_key])
    active_plan_label = (
        _TREATMENT_PLAN_LABELS.get(treatment_key)
        or _PLAN_LABELS.get(decision_path, "Active plan")
    )
    augmented_trace: Dict[str, Any] = {**(trace_evidence or {})}
    if treatment_key:
        augmented_trace["selected_treatment"] = _TREATMENT_LABEL_AND_ICON[treatment_key]["product"]
    augmented_trace["checkpoint_focus"] = _STAGE_CHECKPOINT_FOCUS.get(stage_key, stage_key)
    return FrontendJourneyView(
        hero=FrontendJourneyHero(
            title=hero_title,
            subtitle=subtitle,
            start_date="April 2026",
            next_review=_STAGE_NEXT_REVIEW[stage_key],
            active_plan_label=active_plan_label,
        ),
        progress_strip=FrontendProgressStrip(
            items=[
                FrontendProgressStripItem(label=item["label"], value=item["value"], icon=item["icon"])
                for item in _STAGE_PROGRESS_ITEMS[stage_key]
            ]
        ),
        progress_photos=FrontendProgressPhotos(steps=photo_steps),
        narrative=FrontendJourneyNarrative(
            title=_STAGE_NARRATIVE_TITLES[stage_key],
            text=narrative_body,
        ),
        recommendation=FrontendJourneyRecommendation(
            show=show_recommendation,
            product=treatment_meta["product"] if treatment_meta else None,
            description=treatment_description or None,
            icon=treatment_meta["icon"] if treatment_meta else None,
            requires_medical_approval=requires_medical_approval,
            details=treatment_details,
        ),
        decision_trace_badge=FrontendJourneyTraceBadge(
            label="Decision trace",
            state_label=state_label,
            trace_evidence=augmented_trace,
        ),
    )


def build_frontend_journey_views(
    decision_title: str,
    decision_path: str,
    rules_triggered: List[str] | None = None,
    flags: List[str] | None = None,
    trace_evidence: Dict[str, Any] | None = None,
    priority_factor: str = "",
) -> FrontendJourneyAdapter:
    resolved_rules = rules_triggered or []
    resolved_flags = flags or []
    resolved_evidence = trace_evidence or {}
    treatment_key = _determine_treatment_key(decision_path, priority_factor)
    return FrontendJourneyAdapter(
        month_0=_build_frontend_view("month_0", "Baseline", decision_title, decision_path, resolved_rules, resolved_flags, resolved_evidence, treatment_key),
        week_6=_build_frontend_view("week_6", "Week 6", decision_title, decision_path, resolved_rules, resolved_flags, resolved_evidence, treatment_key),
        month_3=_build_frontend_view("month_3", "Month 3", decision_title, decision_path, resolved_rules, resolved_flags, resolved_evidence, treatment_key),
        month_6=_build_frontend_view("month_6", "Month 6", decision_title, decision_path, resolved_rules, resolved_flags, resolved_evidence, treatment_key),
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
