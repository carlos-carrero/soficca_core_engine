from __future__ import annotations

from typing import Any, Dict, List

from cardio_triage_v1.constants import (
    PATH_ROUTINE,
    PATH_URGENT_SAME_DAY,
    ROUTINE_REVIEW,
    RULE_ROUTINE_STABLE_COMPLETE_V1,
    RULE_URGENT_EXERTIONAL_RADIATION_V1,
    RULE_URGENT_NON_CATASTROPHIC_VITALS_V1,
    RULE_URGENT_SYMPTOM_RISK_CLUSTER_V1,
    URGENT_ESCALATION,
)


def apply_routing(normalized_state: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic non-emergency routing (Stage 4).

    This function assumes readiness-complete and no emergency override yet.
    """
    triggered_rules: List[str] = []
    reasons: List[str] = []

    chest_pain = normalized_state.get("chest_pain_present") is True
    exertional = normalized_state.get("exertional_chest_pain") is True
    radiation_arm_or_jaw = normalized_state.get("radiation_arm_or_jaw") is True
    diaphoresis = normalized_state.get("diaphoresis") is True
    pain_severity = normalized_state.get("pain_severity")
    risk_count = normalized_state.get("cv_risk_factors_count")
    systolic_bp = normalized_state.get("systolic_bp")
    heart_rate = normalized_state.get("heart_rate")

    # Urgent rule 1: exertional chest pain + arm/jaw radiation
    if chest_pain and exertional and radiation_arm_or_jaw:
        triggered_rules.append(RULE_URGENT_EXERTIONAL_RADIATION_V1)
        reasons.append("Exertional chest pain with arm/jaw radiation.")

    # Urgent rule 2: symptom/risk cluster
    severity_high = pain_severity in {"moderate", "high", "severe"}
    if chest_pain and diaphoresis and severity_high and isinstance(risk_count, int) and risk_count >= 2:
        triggered_rules.append(RULE_URGENT_SYMPTOM_RISK_CLUSTER_V1)
        reasons.append("Concerning symptom and cardiovascular risk-factor cluster.")

    # Urgent rule 3: non-catastrophic but abnormal vitals with chest pain
    bp_abnormal = isinstance(systolic_bp, int) and 90 <= systolic_bp <= 99
    hr_abnormal = isinstance(heart_rate, int) and 100 <= heart_rate <= 129
    if chest_pain and (bp_abnormal or hr_abnormal):
        triggered_rules.append(RULE_URGENT_NON_CATASTROPHIC_VITALS_V1)
        reasons.append("Abnormal but non-catastrophic vital signs with chest pain.")

    if triggered_rules:
        return {
            "preliminary_route": PATH_URGENT_SAME_DAY,
            "decision_id": URGENT_ESCALATION,
            "rules_triggered": triggered_rules,
            "reasons": reasons,
        }

    # Routine review fallback for complete, non-emergency, non-urgent cases
    routine_reasons = ["No emergency or urgent cluster detected in complete case."]
    return {
        "preliminary_route": PATH_ROUTINE,
        "decision_id": ROUTINE_REVIEW,
        "rules_triggered": [RULE_ROUTINE_STABLE_COMPLETE_V1],
        "reasons": routine_reasons,
    }
