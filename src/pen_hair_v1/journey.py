from __future__ import annotations

from pen_hair_v1.schema import JourneySection, JourneyView, PenJourneyViews


def _build_view(state_label: str, decision_title: str, decision_path: str) -> JourneyView:
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
            body=f"Deterministic follow-up state for path '{decision_path}'.",
        ),
        recommendation=JourneySection(
            heading="Current recommendation",
            body="Continue topical protocol and monitor tolerance/progress at this milestone.",
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
