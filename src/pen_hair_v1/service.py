from __future__ import annotations

from pen_hair_v1.constants import (
    DECISION_PATH_NEEDS_MORE_INFORMATION,
    DECISION_STATUS_DECIDED,
    DECISION_STATUS_NEEDS_MORE_INFO,
)
from pen_hair_v1.decision_contract import assert_valid_response, build_versions
from pen_hair_v1.journey import build_frontend_journey_views, build_journey_views
from pen_hair_v1.normalization import normalize_intake
from pen_hair_v1.rationale import build_decision_rationale
from pen_hair_v1.rules import select_decision_path
from pen_hair_v1.safety_policy import evaluate_safety
from pen_hair_v1.schema import (
    DecisionPath,
    FrontendAdapter,
    FrontendEvaluationAdapter,
    FrontendJourneyAdapter,
    PenDecision,
    PenEvaluationResponse,
    PenIntakeRequest,
    PenTrace,
)
from pen_hair_v1.trace import build_trace_evidence, rules_evaluated
from pen_hair_v1.validation import validate_intake


def evaluate_pen_intake(payload: PenIntakeRequest) -> PenEvaluationResponse:
    validated = validate_intake(payload)
    normalized = normalize_intake(validated)

    safety = evaluate_safety(normalized)
    selected = select_decision_path(normalized, safety)
    decision_status = (
        DECISION_STATUS_NEEDS_MORE_INFO
        if selected["decision_path"] == DECISION_PATH_NEEDS_MORE_INFORMATION
        else DECISION_STATUS_DECIDED
    )

    decision = PenDecision(
        status=decision_status,
        decision_path=DecisionPath(selected["decision_path"]),
        title=selected["title"],
        explanation=selected["explanation"],
        flags=safety["flags"],
        excluded_options=[DecisionPath(option) for option in selected["excluded_options"]],
    )
    decision_rationale = build_decision_rationale(decision, normalized)

    trace = PenTrace(
        rules_evaluated=rules_evaluated(),
        rules_triggered=selected["rules_triggered"],
        trace_evidence=build_trace_evidence(normalized),
    )
    journey_views = build_journey_views(
        decision_title=decision.title,
        decision_path=decision.decision_path.value,
        rules_triggered=selected["rules_triggered"],
        flags=decision.flags,
    )

    response = PenEvaluationResponse(
        versions=build_versions(),
        decision=decision,
        decision_rationale=decision_rationale,
        trace=trace,
        journey_views=journey_views,
        frontend_adapter=FrontendAdapter(
            evaluation=FrontendEvaluationAdapter(
                decision_path=decision.decision_path,
                decision_title=decision.title,
                decision_explanation=decision.explanation,
                trace_evidence=trace.trace_evidence,
            ),
            journey=build_frontend_journey_views(
                decision_title=decision.title,
                decision_path=decision.decision_path.value,
                rules_triggered=selected["rules_triggered"],
                flags=decision.flags,
                trace_evidence=trace.trace_evidence,
                priority_factor=normalized.priority_factor,
            ),
        ),
    )
    return assert_valid_response(response)
