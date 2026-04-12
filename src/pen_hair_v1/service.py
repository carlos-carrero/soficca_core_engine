from __future__ import annotations

from pen_hair_v1.constants import DECISION_STATUS_DECIDED
from pen_hair_v1.decision_contract import assert_valid_response, build_versions
from pen_hair_v1.journey import build_journey_views
from pen_hair_v1.normalization import normalize_intake
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
    selected = select_decision_path(normalized, safety["excluded_options"])

    decision = PenDecision(
        status=DECISION_STATUS_DECIDED,
        decision_path=DecisionPath(selected["decision_path"]),
        title=selected["title"],
        explanation=selected["explanation"],
        flags=safety["flags"],
        excluded_options=[DecisionPath(option) for option in selected["excluded_options"]],
    )

    trace = PenTrace(
        rules_evaluated=rules_evaluated(),
        rules_triggered=selected["rules_triggered"],
        trace_evidence=build_trace_evidence(normalized),
    )
    journey_views = build_journey_views(
        decision_title=decision.title,
        decision_path=decision.decision_path.value,
    )

    response = PenEvaluationResponse(
        versions=build_versions(),
        decision=decision,
        trace=trace,
        journey_views=journey_views,
        frontend_adapter=FrontendAdapter(
            evaluation=FrontendEvaluationAdapter(
                decision_path=decision.decision_path,
                decision_title=decision.title,
                decision_explanation=decision.explanation,
                trace_evidence=trace.trace_evidence,
            ),
            journey=FrontendJourneyAdapter(
                month_0=journey_views.month_0,
                week_6=journey_views.week_6,
                month_3=journey_views.month_3,
                month_6=journey_views.month_6,
            ),
        ),
    )
    return assert_valid_response(response)
