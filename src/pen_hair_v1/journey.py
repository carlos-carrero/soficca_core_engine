from __future__ import annotations

from pen_hair_v1.constants import (
    DECISION_PATH_MANUAL_REVIEW,
    DECISION_PATH_NEEDS_MORE_INFORMATION,
    DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT,
)
from pen_hair_v1.schema import JourneySection, JourneyView, PenJourneyViews


def _build_view(state_label: str, decision_title: str, decision_path: str) -> JourneyView:
    recommendation_body = "Continue topical protocol and monitor tolerance/progress at this milestone."
    narrative_body = f"Deterministic follow-up state for path '{decision_path}'."

    if decision_path == DECISION_PATH_TOPICAL_TREATMENT_WITH_SUPPORT:
        recommendation_body = "Continue topical plan with adherence/comfort support and close check-ins."
        narrative_body = "Topical pathway selected with additional support for tolerance and consistency."
    elif decision_path == DECISION_PATH_MANUAL_REVIEW:
        recommendation_body = "Pause auto-plan activation and complete clinician manual review before proceeding."
        narrative_body = "Case requires manual review; journey milestones track review and safe next-step alignment."
    elif decision_path == DECISION_PATH_NEEDS_MORE_INFORMATION:
        recommendation_body = "Collect missing preference/consistency details before treatment activation."
        narrative_body = "Decision deferred pending critical missing information."

    return JourneyView(
        hero=JourneySection(
            heading=state_label,
            body=f"Plan status anchored to {decision_title.lower()}.",
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
        decision_trace_badge="Deterministic safety-first decision",
    )


def build_journey_views(decision_title: str, decision_path: str) -> PenJourneyViews:
    return PenJourneyViews(
        month_0=_build_view("Baseline / Activation", decision_title, decision_path),
        week_6=_build_view("Week 6 Check-in", decision_title, decision_path),
        month_3=_build_view("Month 3 Progress", decision_title, decision_path),
        month_6=_build_view("Month 6 Review", decision_title, decision_path),
    )
