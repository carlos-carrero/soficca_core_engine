from __future__ import annotations

from typing import Any, Dict, List

from cardio_triage_v1.constants import (
    FLAG_DYSPNEA_CHEST_PAIN_HIGH_RISK,
    FLAG_SEVERE_ONGOING_CHEST_PAIN,
    FLAG_SYNCOPAL_CHEST_PAIN,
    FLAG_TACHYCARDIA_WITH_CONCERNING_SYMPTOMS,
    FLAG_VERY_LOW_SBP,
    POLICY_DYSPNEA_CHEST_PAIN_HIGH_RISK_V1,
    POLICY_SEVERE_ONGOING_CHEST_PAIN_V1,
    POLICY_SYNCOPAL_CHEST_PAIN_V1,
    POLICY_TACHYCARDIA_WITH_CONCERNING_SYMPTOMS_V1,
    POLICY_VERY_LOW_BP_V1,
)


def evaluate_safety(normalized_state: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic hard red-flag emergency policy (Stage 3 only)."""
    activated_rules: List[str] = []
    flags: List[str] = []

    chest_pain = normalized_state.get("chest_pain_present") is True
    syncope = normalized_state.get("syncope") is True
    dyspnea = normalized_state.get("dyspnea") is True
    pain_duration = normalized_state.get("pain_duration_minutes")
    pain_character = normalized_state.get("pain_character")
    systolic_bp = normalized_state.get("systolic_bp")
    heart_rate = normalized_state.get("heart_rate")
    prior_mi = normalized_state.get("prior_mi") is True
    known_cad = normalized_state.get("known_cad") is True

    # 1) syncope + active chest pain
    if syncope and chest_pain:
        activated_rules.append(POLICY_SYNCOPAL_CHEST_PAIN_V1)
        flags.append(FLAG_SYNCOPAL_CHEST_PAIN)

    # 2) severe ongoing chest pain
    severe_labels = {"severe", "crushing", "heavy", "worst"}
    if chest_pain and pain_character in severe_labels and isinstance(pain_duration, int) and pain_duration >= 20:
        activated_rules.append(POLICY_SEVERE_ONGOING_CHEST_PAIN_V1)
        flags.append(FLAG_SEVERE_ONGOING_CHEST_PAIN)

    # 3) very low systolic BP
    if isinstance(systolic_bp, int) and systolic_bp < 90:
        activated_rules.append(POLICY_VERY_LOW_BP_V1)
        flags.append(FLAG_VERY_LOW_SBP)

    # 4) very high heart rate with concerning symptoms
    if isinstance(heart_rate, int) and heart_rate >= 130 and (chest_pain or dyspnea or syncope):
        activated_rules.append(POLICY_TACHYCARDIA_WITH_CONCERNING_SYMPTOMS_V1)
        flags.append(FLAG_TACHYCARDIA_WITH_CONCERNING_SYMPTOMS)

    # 5) dyspnea + chest pain in high-risk combination
    if chest_pain and dyspnea and (prior_mi or known_cad):
        activated_rules.append(POLICY_DYSPNEA_CHEST_PAIN_HIGH_RISK_V1)
        flags.append(FLAG_DYSPNEA_CHEST_PAIN_HIGH_RISK)

    has_red_flags = len(activated_rules) > 0
    return {
        "has_red_flags": has_red_flags,
        "override_applied": has_red_flags,
        "severity": "EMERGENCY" if has_red_flags else "NONE",
        "flags": flags,
        "activated_rules": activated_rules,
        "override_reason": "Hard red-flag emergency criteria met." if has_red_flags else None,
    }
